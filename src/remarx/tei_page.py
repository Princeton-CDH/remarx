#!/usr/bin/env python
"""
Script to extract TEI content between two pages as plain text and
save it to a file.  The script takes a path to an input TEI/XML file,
start and end page numbers, and the name of an output file to create.

The start and end page numbers should match n attributes on <pb> tags
in the input document.

Example usage:

    python tei_page.py tei_doc.xml  -s 12 -e 14 page12-13.txt


This will extract text content between `<pb n="12"/>` and `<pb n="14"/>`
as lines of text and save them to a new file named `page12.txt`.

If the end page number is not specified, the script will assume
end page is start page + 1 (only works for numeric pages). Example:

    python tei_page.py tei_doc.xml  -s 12  page12.txt


"""

import argparse
import pathlib
import re
import sys
from collections import namedtuple
from typing import Iterable

from lxml import etree

TEI_NAMESPACE = "http://www.tei-c.org/ns/1.0"

# namespaced tags look like {http://www.tei-c.org/ns/1.0}tagname
# create a named tuple of short tag name -> namespaced tag name
_tei_tags = ["pb", "lb", "note", "add", "label"]
TagNames = namedtuple("TagNames", _tei_tags)
TEI_TAG = TagNames(**{tag: "{%s}%s" % (TEI_NAMESPACE, tag) for tag in _tei_tags})


def text_between_pages(element: etree._Element, start: str, end: str) -> Iterable[str]:
    """generator of text strings between this page beginning tag and
    the next one"""

    # don't output content until we hit the page indicating
    # start of desired content
    started = False

    # add a newline to output before specific tags
    newline_before_tags = [TEI_TAG.lb, TEI_TAG.note]

    # iterate and yield text between start and end pages
    for text in element.xpath(".//text()"):
        parent = text.getparent()

        # yield newline for a line break tag or note
        if started and text.is_tail and parent.tag in newline_before_tags:
            yield "\n"

        # if we hit a pb tag, check the n attribute for start/ end condition
        if text.is_tail and parent.tag == TEI_TAG.pb:
            # for marx, limit to pb that are for the manuscript edition

            # mega-specific: there are two sets of page numbers, we want
            # the main pagination, not the editorial manuscript pagination
            if parent.get("ed") is None:
                # found the starting pb tag
                if parent.get("n") == start:
                    # set flag to start yielding text content after this point
                    started = True
                # found the ending pb tag; stop iterating
                if parent.get("n") == end:
                    break

        # check for editorial text content (e.g. original page numbers)
        if started and (
            parent.tag == TEI_TAG.add
            or (parent.tag == TEI_TAG.label and parent.get("type") == "mpb")
        ):
            # omit if text is inside an editorial tag (is_text)
            # OR if text comes immediately after (is_tail) and is whitespace only
            if text.is_text or text.is_tail and re.match(r"^\s+$", text):
                continue

        # yield text if we are after the start page
        if started:
            # remove trailing whitespace if it includes a newline
            # (i.e., space between indented tags in the XML)
            yield re.sub(r"\s*\n\s*", " ", text)


def find_common_ancestor(el1: etree._Element, el2: etree._Element) -> etree._Element:
    """Find and return the nearest common ancestor for
    two elements in the same document."""
    # get a list of ancestors for the first element
    el1_ancestors = list(el1.iterancestors())

    # iterate over ancestors for the second element
    # and return the first one that is in the other list
    for el2_ancestor in el2.iterancestors():
        if el2_ancestor in el1_ancestors:
            return el2_ancestor


def get_pages(doc: etree._Element, start: str, end: str) -> str:
    # use the start and end page numbers to find the elements of interest
    start_pb = end_pb = None
    # iterative find is faster than xpath since it does not need to load
    # the whole document
    for pb in doc.iterfind(".//{%s}pb[@n]" % TEI_NAMESPACE):
        # use string-comparison since attributes are strings
        # and not all n attributes are numeric
        if pb.get("n") == start:
            start_pb = pb
        if pb.get("n") == end:
            end_pb = pb
        # bail out once we find both
        if start_pb is not None and end_pb is not None:
            break

    error_msg = []
    if start_pb is None:
        error_msg.append(f"start page '{start}' not found")
    if end_pb is None:
        error_msg.append(f"end page '{end}' not found")

    if error_msg:
        raise ValueError(f"Specified page range not found: {'; '.join(error_msg)}.")

    assert isinstance(start_pb, etree._Element)
    assert isinstance(end_pb, etree._Element)
    # find the nearest common ancestor so that we can query for all
    # text nodes needed to get all content between the requested pages
    common_ancestor = find_common_ancestor(start_pb, end_pb)

    # get text between start/end
    text_lines = list(text_between_pages(common_ancestor, start, end))
    print(f"Extracted {len(text_lines)} lines of text.")

    return "".join(text_lines)


def main():
    parser = argparse.ArgumentParser(
        description="Extract a specific page range of text from a TEI XML document",
    )
    parser.add_argument(
        "tei_file",
        type=pathlib.Path,
        help="Path to source TEI/XML file",
    )
    parser.add_argument(
        "-s",
        "--start",
        dest="start_page",
        type=str,
        help="Page number (pb n attribute) to indicate start of text content",
        required=True,
    )
    parser.add_argument(
        "-e",
        "--end",
        dest="end_page",
        type=str,
        help="Page number indicating end of text content (not inclusive);"
        + "if unset, assumes a single page (start + 1)",
        required=False,
    )
    parser.add_argument(
        "output",
        help="Filename where the output should be saved",
        type=pathlib.Path,
    )
    args = parser.parse_args()

    # Check input paths exist when they should and don't when they shouldn't
    if not args.tei_file.is_file():
        print(f"Error: TEI file {args.tei_file} does not exist", file=sys.stderr)
        sys.exit(1)
    if args.output.is_file():
        print(
            f"Error: output file {args.output} exists. Will not overwrite.",
            file=sys.stderr,
        )
        sys.exit(1)

    # if end page is not specified, set end to start + 1
    try:
        end_page = args.end_page or str(int(args.start_page) + 1)
    except ValueError:
        # error if if end is unset and start cannot be converted to integer
        print(
            f"Error determining end page from start page '{args.start_page}'",
            file=sys.stderr,
        )
        sys.exit(1)

    doc = etree.parse(args.tei_file)

    with args.output.open("w") as outfile:
        try:
            outfile.write(get_pages(doc, args.start_page, end_page))
        except ValueError as err:
            # display any error message, then continue on to cleanup
            print(err, file=sys.stderr)

    # check if file is zero size (something went wrong)
    # remove and report the empty file
    if args.output.stat().st_size == 0:
        print("No text output; file not created.", file=sys.stderr)
        args.output.unlink()


if __name__ == "__main__":
    main()
