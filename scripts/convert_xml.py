"""
Reads a specified MEGA TEI/XML file and outputs text files, one per page,
to a specified directory.

Example Usage:
    python scripts/convert_xml.py "texts/MEGA_xml/MEGA_A2_B005-00_ETX.xml 11-46-21-885.xml" texts/MEGA_texts
"""

import argparse
import pathlib
import re
import sys
from collections import namedtuple
from collections.abc import Generator
from functools import cached_property
from typing import ClassVar, NamedTuple, Self

from lxml.etree import XMLSyntaxError, _Element
from neuxml import xmlmap

TEI_NAMESPACE = "http://www.tei-c.org/ns/1.0"

# namespaced tags look like {http://www.tei-c.org/ns/1.0}tagname
# create a named tuple of short tag name -> namespaced tag name
TagNames: NamedTuple = namedtuple(
    "TagNames", ("pb", "lb", "note", "add", "label", "ref", "div3")
)
TEI_TAG = TagNames(**{tag: f"{{{TEI_NAMESPACE}}}{tag}" for tag in TagNames._fields})
"Convenience access to namespaced TEI tag names"


class BaseTEIXmlObject(xmlmap.XmlObject):
    """
    Base class for TEI XML objects with TEI namespace included in root namespaces,
    for use in XPath expressions.
    """

    ROOT_NAMESPACES: ClassVar[dict[str, str]] = {"t": TEI_NAMESPACE}


class TEIPage(BaseTEIXmlObject):
    """
    Custom :class:`eulxml.xmlmap.XmlObject` instance for a page
    of content within a TEI XML document.
    """

    number = xmlmap.StringField("@n")
    "page number"
    edition = xmlmap.StringField("@ed")
    "page edition, if any"

    # page beginning tags delimit content instead of containing it;
    # use following axis to find all text nodes following this page beginning
    text_nodes = xmlmap.StringListField("following::text()")
    "list of all text nodes following this tag"

    # fetch footnotes after the current page break; will filter them in Python later
    # pb is a delimiter (not a container), so "following::note" returns all later footnotes
    following_footnotes = xmlmap.NodeListField(
        "following::t:note[@type='footnote']", xmlmap.XmlObject
    )
    "list of footnote elements within this page and following pages"

    next_page = xmlmap.NodeField(
        "following::t:pb[not(@ed)][1]",
        "self",
    )
    "the next standard page break after this one, or None if this is the last page"

    @staticmethod
    def is_footnote_content(el: _Element) -> bool:
        """
        Helper function that checks if an element or any of its ancestors is footnote content.
        """
        if (
            el.tag in [TEI_TAG.ref, TEI_TAG.note]
            and el.attrib.get("type") == "footnote"
        ):
            return True
        return any(
            TEIPage.is_footnote_content(ancestor) for ancestor in el.iterancestors()
        )

    def get_page_footnotes(self) -> list[xmlmap.XmlObject]:
        """
        Filters footnotes to keep only the footnotes that belong to this page.
        Only includes footnotes that occur between this pb and the next standard pb[not(@ed)].
        """
        page_footnotes: list[xmlmap.XmlObject] = []

        for footnote in self.following_footnotes:
            # If we have a next page and this footnote belongs to it, we're done
            if self.next_page and footnote in self.next_page.following_footnotes:
                break
            page_footnotes.append(footnote)

        return page_footnotes

    def get_body_text(self) -> str:
        """
        Extract body text content for this page, excluding footnotes and editorial content.
        """
        body_text_parts = []
        for text in self.text_nodes:
            # text here is an lxml smart string, which preserves context
            # in the xml tree and is associated with a parent tag.
            parent = text.getparent()

            # stop iterating when we hit the next page break;
            if self.next_page and parent == self.next_page.node:
                break

            # Skip this text node if it's inside a footnote tag
            if self.is_footnote_content(parent):
                continue

            # omit editorial content (e.g. original page numbers)
            if (
                parent.tag == TEI_TAG.add
                or (parent.tag == TEI_TAG.label and parent.get("type") == "mpb")
            ) and (text.is_text or (text.is_tail and text.strip() == "")):
                # omit if text is inside an editorial tag (is_text)
                # OR if text comes immediately after (is_tail) and is whitespace only
                continue

            body_text_parts.append(text)

        # consolidate whitespace once after joining all parts
        # (i.e., space between indented tags in the XML)
        return re.sub(r"\s*\n\s*", "\n", "".join(body_text_parts)).strip()

    def get_individual_footnotes(self) -> Generator[str]:
        """
        Get individual footnote content as a generator.
        Yields each footnote's text content individually as a separate string element.
        Each yielded element corresponds to one complete footnote from the page.
        """
        for footnote in self.get_page_footnotes():
            footnote_text = str(footnote).strip()
            # consolidate whitespace for footnotes
            footnote_text = re.sub(r"\s*\n\s*", "\n", footnote_text)
            yield footnote_text

    def get_footnote_text(self) -> str:
        """
        Get all footnote content as a single string, with footnotes separated by double newlines.
        """
        return "\n\n".join(self.get_individual_footnotes())

    def __str__(self) -> str:
        """
        Page text contents as a string, with body text and footnotes.
        """
        return f"{self.get_body_text()}\n\n{self.get_footnote_text()}"


class TEIDocument(BaseTEIXmlObject):
    """
    Custom :class:`eulxml.xmlmap.XmlObject` instance for TEI XML document.
    Customized for MEGA TEI XML.
    """

    all_pages = xmlmap.NodeListField("//t:text//t:pb", TEIPage)
    """List of page objects, identified by page begin tag (pb). Includes all
    pages (standard and manuscript edition), because the XPath is significantly
    faster without filtering."""

    @cached_property
    def pages(self) -> list[TEIPage]:
        """
        Standard pages for this document.  Returns a list of TEIPage objects
        for this document, omitting any pages marked as manuscript edition.
        """
        # it's more efficient to filter in python than in xpath
        return [page for page in self.all_pages if page.edition != "manuscript"]

    @classmethod
    def init_from_file(cls, path: pathlib.Path) -> Self:
        """
        Class method to initialize a new :class:`TEIDocument` from a file.
        """
        try:
            return xmlmap.load_xmlobject_from_file(path, cls)
        except XMLSyntaxError as err:
            raise ValueError(f"Error parsing {path} as XML") from err


def convert_xml_to_text_files(
    xml_file_path: pathlib.Path, output_dir: pathlib.Path
) -> None:
    """
    Convert a MEGA TEI/XML file to text files organized by page.

    Args:
        xml_file_path: Path to the input XML file
        output_dir: Directory where text files will be written
    """
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Parse the XML document
    try:
        doc = TEIDocument.init_from_file(xml_file_path)
    except Exception as e:
        print(f"Error parsing XML file {xml_file_path}: {e}")
        sys.exit(1)

    print(f"Processing {len(doc.pages)} pages from {xml_file_path.name}")

    # Process each page and write to separate files
    for i, page in enumerate(doc.pages):
        # Get the full page content (body text + footnotes)
        page_content = str(page)

        if page_content.strip():  # Only write non-empty pages
            # Use page number if available, otherwise use sequential numbering
            page_num = page.number if page.number else str(i + 1)
            output_file = output_dir / f"page_{page_num.zfill(3)}.txt"

            with open(output_file, "w", encoding="utf-8") as f:
                f.write(page_content)

            print(f"Written page {page_num} to {output_file.name}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "xml_file",
        type=pathlib.Path,
    )
    parser.add_argument(
        "output_dir",
        type=pathlib.Path,
    )

    args = parser.parse_args()

    xml_file = args.xml_file
    output_dir = args.output_dir

    # Check if input file exists
    if not xml_file.exists():
        print(f"Error: Input file {xml_file} not found.")
        sys.exit(1)

    print(f"Converting {xml_file} to text files in {output_dir}")
    convert_xml_to_text_files(xml_file, output_dir)
    print("Conversion completed!")


if __name__ == "__main__":
    main()
