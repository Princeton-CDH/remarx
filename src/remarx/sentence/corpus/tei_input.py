"""
Functionality related to parsing MEGA TEI/XML content with the
goal of creating a sentence corpora with associated metadata
from the TEI.
"""

import pathlib
import re
from collections import namedtuple
from collections.abc import Generator
from dataclasses import dataclass, field
from functools import cached_property
from typing import ClassVar, NamedTuple, Self

from lxml.etree import XMLSyntaxError
from neuxml import xmlmap

from remarx.sentence.corpus.text_input import TextInput

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

    def text_contents(self) -> Generator[tuple[str, str]]:
        """
        Generator of text content on this page, between the current
        and following page begin tags.  MEGA specific logic:
        ignores page indicators for the manuscript edition
        (<pb> tags with ed="manuscript"); assumes standard pb tags have no edition.
        Returns two chunks per page: body text and footnotes.
        Note: Footnotes that span multiple pages are ignored for now.
        """
        # Extract body text (ignore partial content, hyphenation, etc.)
        body_text_parts = []
        for text in self.text_nodes:
            # text here is an lxml smart string, which preserves context
            # in the xml tree and is associated with a parent tag.
            parent = text.getparent()
            # stop iterating when we hit the next page break;
            if (
                parent != self.node  # not the current pb tag
                and parent.tag == TEI_TAG.pb
                # ignore alternate edition page breaks (MEGA specific)
                and parent.get("ed") is None
            ):
                break

            # Skip the current text node if it's inside a footnote
            ancestor = parent
            while ancestor is not None:
                if ancestor.tag == TEI_TAG.note and ancestor.get("type") == "footnote":
                    break
                ancestor = ancestor.getparent()
            else:
                # omit editorial content (e.g. original page numbers)
                if (
                    parent.tag == TEI_TAG.add
                    or (parent.tag == TEI_TAG.label and parent.get("type") == "mpb")
                ) and (text.is_text or (text.is_tail and text.strip() == "")):
                    # omit if text is inside an editorial tag (is_text)
                    # OR if text comes immediately after (is_tail) and is whitespace only
                    continue

                # consolidate whitespace if it includes a newline
                # (i.e., space between indented tags in the XML)
                body_text_parts.append(re.sub(r"\s*\n\s*", "\n", text))

        # Yield body text as first chunk
        body_text = "".join(body_text_parts).strip()
        if body_text:
            yield (body_text, "text")

        # Extract and yield combined footnotes as second chunk
        notes = self.node.xpath(
            "following::t:note[@type='footnote'][not(.//t:pb[not(@ed)])]",
            namespaces=self.ROOT_NAMESPACES,
        )

        if notes:
            footnote_texts = []
            for note in notes:
                footnote_text = "".join(
                    note.xpath(".//text()", namespaces=self.ROOT_NAMESPACES)
                ).strip()
                if footnote_text:
                    footnote_texts.append(footnote_text)

            if footnote_texts:
                yield ("\n\n".join(footnote_texts), "footnote")

    def __str__(self) -> str:
        """
        Page text contents as a string
        """
        # Extract just the text content from the tuples
        return "".join(text for text, section_type in self.text_contents())


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


@dataclass
class TEIinput(TextInput):
    """
    Input class for TEI/XML content.  Takes a single input file,
    and yields text content by page, with page number.
    Customized for MEGA TEI/XML: follows standard edition page numbering
    and ignores pages marked as manuscript edition.
    """

    xml_doc: TEIDocument = field(init=False)
    "Parsed XML document; initialized from inherited input_file"

    field_names: tuple[str, ...] = (
        *TextInput.field_names,
        "page_number",
        "section_type",
    )
    "List of field names for sentences from TEI XML input files"

    def __post_init__(self) -> None:
        """
        After default initialization, parse [input_file][remarx.sentence.corpus.text_input.TextInput.input_file]
        as a [TEIDocument][remarx.sentence.corpus.tei_input.TEIDocument] and store as
        [xml_doc][remarx.sentence.corpus.tei_input.TEIinput.xml_doc].
        """
        # parse the input file as xml and save the result
        self.xml_doc = TEIDocument.init_from_file(self.input_file)

    def get_text(self) -> Generator[dict[str, str]]:
        """
        Get document content as plain text. Chunked by page and section type
        (body text & footnotes), with page number and section type.

        :returns: Generator with a dictionary of text content by page section,
        including page number and section_type ("text" or "footnote").
        """
        # yield body text and footnotes content chunked by page with page number
        for page in self.xml_doc.pages:
            for text_content, section_type in page.text_contents():
                yield {
                    "text": text_content,
                    "page_number": page.number,
                    "section_type": section_type,
                }
