"""
Script for transforming an html page into a plaintext file.

NOTE: This script is tailored specifically for the Communist Manifesto webpages.

Example Usage:

    `uv run python parse_html.py in_html out_txt`
"""

import argparse
import pathlib
import re
import sys

from bs4 import BeautifulSoup, NavigableString, Tag


def get_tag_text(tag: Tag) -> str:
    """
    Generates the text for a given Beautiful Tag. Hyperlinks are ignored.

    :returns: str of the tag's generated text
    """
    out_text = ""
    for child_elt in tag.children:
        if isinstance(child_elt, NavigableString):
            out_text += child_elt
        else:
            # Skip hyperlink tags
            if child_elt.name != "a":
                out_text += child_elt.get_text()
    # Combine consecutive spaces & strip leading and trailing whitespace
    return re.sub(r"  *", " ", out_text).strip()


def get_html_text(in_html: pathlib.Path) -> str:
    """
    Extracts the text from the input html file. Footnotes are ignored.

    :returns: str of the extracted text for `in_html`
    """
    soup = BeautifulSoup(in_html.read_text(), "html.parser")
    body_soup = soup.body

    # Find starting paragraph text
    start_p = body_soup.find("p", class_="fst")

    # Start at previous section (h3) or title (h1) header
    start_elt = start_p.find_previous(re.compile(r"^h[1,3]"))
    text = get_tag_text(start_elt) + "\n\n"

    # Add each following element's text until the notes section is reached
    # Notes section is an h3 tag with text "Anmerkungen"
    for elt in start_elt.next_siblings:
        # Skip NavigableStrings
        if isinstance(elt, NavigableString):
            continue

        tag_name = elt.name
        tag_text = get_tag_text(elt).strip()

        # Stop when the notes section is reached
        if tag_name == "h3" and tag_text.startswith("Anmerkung"):
            break

        if tag_name == "p":
            # Case: Paragraphs
            if not tag_text or ("class" in elt and elt["class"] == "link"):
                # Skip tags without non-whitespace text or with links
                continue
            text += f"{tag_text}\n\n"
        elif re.fullmatch(r"h\d", tag_name):
            # Case: Headers
            text += f"{tag_text}\n\n"
        elif tag_name == "ol":
            # Case: Ordered lists
            for i, list_elt in enumerate(elt.find_all("li", recursive=False)):
                text += f"{i + 1}. {get_tag_text(list_elt)}\n"
            text += "\n"
        else:
            print(f"Warning: Skipping unsupported tag {tag_name}")
    return text.strip()


def write_html_text(in_html: pathlib.Path, out_txt: pathlib.Path) -> None:
    """
    Extracts the text from the input html file and saves the resulting file at
    the specified filepath. Calls :meth:`get_html_text`.

    :raises ValueError: if `in_html` does not exist
    :raises ValueError: if `out_txt` already exists
    """
    # Validate input args
    if not in_html.is_file():
        raise ValueError("Input file does not exist")
    if out_txt.is_file():
        raise ValueError("Output file exists. Not overwriting.")

    out_txt.write_text(get_html_text(in_html))


def main() -> None:
    """
    Command-line access for extracting the text from an html page
    """
    parser = argparse.ArgumentParser(
        description="Extract the text from a given html page and save as a plaintext file",
    )
    parser.add_argument(
        "in_file",
        type=pathlib.Path,
        help="Path to input html file",
    )
    parser.add_argument(
        "out_txt",
        type=pathlib.Path,
        help="Path to output plaintext file",
    )

    args = parser.parse_args()
    try:
        write_html_text(args.in_file, args.out_txt)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
