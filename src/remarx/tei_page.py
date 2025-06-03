#!/usr/bin/env python
"""
Script to extract TEI content between two pages as plain text and
save it to a file.  The script takes a path to an input TEI/XML file,
start and end page numbers, and the name of an output file to create.

The start and end page numbers should match n attributes on <pb> tags
in the input document. These <pb> tags indicate the bounds for the content
to be included; content from the ending page is _not_ included.

Example usage:

    python tei_page.py tei_doc.xml -s 12 -e 14 -o page12-13.txt


This will extract text content between `<pb n="12"/>` and `<pb n="14"/>`
as lines of text and save them to a new file named `page12.txt`.

If the end page number is not specified, the script will assume
end page is start page + 1 (only works for numeric pages). Example:

    python tei_page.py tei_doc.xml -s 12 -o page12.txt

Additional options:
- `-l` or `--line-numbers`: include XML line numbers at the beginning of each line


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
_tei_tags = ["pb", "lb", "note", "add", "label", "ref", "div3"]
TagNames = namedtuple("TagNames", _tei_tags)
TEI_TAG = TagNames(**{tag: "{%s}%s" % (TEI_NAMESPACE, tag) for tag in _tei_tags})


def is_footnote_content(el: etree._Element) -> bool:
    if el.tag in [TEI_TAG.ref, TEI_TAG.note] and el.attrib["type"] == "footnote":
        return True
    return any([is_footnote_content(el) for el in el.iterancestors()])


def text_between_pages(
    element: etree._Element,
    start: str,
    end: str,
    line_numbers: bool = False,
    include_footnotes: bool = True,
) -> Iterable[str]:
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
        if started and text.is_tail:
            if parent.tag in newline_before_tags and (
                include_footnotes or not is_footnote_content(parent)
            ):
                yield "\n"

                if line_numbers and parent.tag == TEI_TAG.lb:
                    # when line numbers are requested, output right-justified line number
                    # with two spaces before the line of text

                    yield f"{parent.attrib['n']:>2}  "

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
            # if include footnotes has been turned off, check if content should be skipped
            if not include_footnotes:
                # if text is directly inside something under a footnote element
                # or if text is nested under a a footnote element
                if (text.is_text and is_footnote_content(parent)) or (
                    text.is_tail and is_footnote_content(parent.getparent())
                ):
                    # skip this text content
                    continue

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


def get_pages(
    doc: etree._Element,
    start: str,
    end: str,
    line_numbers: bool = False,
    include_footnotes: bool = True,
) -> str:
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
    text_lines = list(
        text_between_pages(
            common_ancestor,
            start,
            end,
            line_numbers=line_numbers,
            include_footnotes=include_footnotes,
        )
    )
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
        "-l",
        "--line-numbers",
        action="store_true",
        help="Output XML line numbers at the beginning of each line (off by default)",
        default=False,
    )
    parser.add_argument(
        "--footnotes",
        action=argparse.BooleanOptionalAction,
        help="Use to control whether output text should include footnote markers and content (default: %(default)s)",
        default=True,
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Filename where the output should be saved; if not specified, prints extracted text to stdout",
        type=pathlib.Path,
        required=False,
    )
    args = parser.parse_args()

    # Check input paths exist when they should and don't when they shouldn't
    if not args.tei_file.is_file():
        print(f"Error: TEI file {args.tei_file} does not exist", file=sys.stderr)
        sys.exit(1)
    if args.output is not None and args.output.is_file():
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

    try:
        text_content = get_pages(
            doc,
            args.start_page,
            end_page,
            line_numbers=args.line_numbers,
            include_footnotes=args.footnotes,
        )
    except ValueError as err:
        # display any error message, then continue on to cleanup
        print(err, file=sys.stderr)
        sys.exit(1)

    if text_content:
        if args.output:
            with args.output.open("w") as outfile:
                outfile.write(text_content)
        else:
            print(text_content)
    else:
        print("No text output.", file=sys.stderr)


if __name__ == "__main__":
    main()
