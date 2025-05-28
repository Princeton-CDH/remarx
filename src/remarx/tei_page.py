#!/usr/bin/env python
"""
Script to extract TEI content between two pages as plain text and
save it to a file.  The script takes a path to an input TEI/XML file,
start and end page numbers, and the name of an output file to create.

The start and end page numbers should match n attributes on <pb> tags
in the input document.

Example usage:

    python tei_page.py tei_doc.xml  12 13 page12.txt


This will extract all content between `<pb n="12"/>` and `<pb n="13"/>`
as lines of text and save them to a new file named `page12.txt`.

"""

import argparse
import pathlib
import re
import sys
from typing import Iterable

from lxml import etree

TEI_NAMESPACE = "http://www.tei-c.org/ns/1.0"


def text_between_pages(element: etree._Element, start: str, end: str) -> Iterable[str]:
    """generator of text strings between this page beginning tag and
    the next one"""

    # don't output content until we hit the page indicating
    # start of desired content
    started = False

    # iterate and yield text between start and end pages
    for text in element.xpath(".//text()"):
        parent = text.getparent()

        # yield newline for a line break tag
        if started and text.is_tail and parent.tag == "{%s}lb" % TEI_NAMESPACE:
            yield "\n"

        # if we hit a pb tag, check the n attribute for start/ end condition
        if text.is_tail and parent.tag == "{%s}pb" % TEI_NAMESPACE:
            # found the starting pb tag
            if parent.get("n") == start:
                # set flag to start yielding text content after this point
                started = True
            # found the ending pb tag; stop iterating
            if parent.get("n") == end:
                break

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
        "start_page",
        type=str,
        help="Page number (pb n attribute) to indicate start of text content",
    )
    parser.add_argument(
        "end_page", type=str, help="Page number for end of text content"
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

    doc = etree.parse(args.tei_file)

    with args.output.open("w") as outfile:
        try:
            outfile.write(get_pages(doc, args.start_page, args.end_page))
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
