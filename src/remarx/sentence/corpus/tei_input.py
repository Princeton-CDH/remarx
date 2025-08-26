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

from lxml.etree import XMLSyntaxError, _Element
from neuxml import xmlmap

from remarx.sentence.corpus.base_input import FileInput, SectionType

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

    # fetch all footnotes after the current page break; will filter them in Python later
    # pb is a delimiter (not a container), so "following::note" returns all later footnotes
    all_following_footnotes = xmlmap.NodeListField(
        "following::t:note[@type='footnote']", xmlmap.XmlObject
    )
    "list of all footnote elements within this page and following pages"

    next_page = xmlmap.NodeField(
        "following::t:pb[not(@ed)][1]",
        "self",
    )
    """The next standard page break after this one, or None if this is the last page."""

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
        # Use the next_page property to find the next standard page break
        next_page_node = self.next_page.node if self.next_page else None

        # If there is a next page break, only include footnotes that occur before it
        if next_page_node is not None:
            page_footnotes: list[xmlmap.XmlObject] = []
            for footnote in self.all_following_footnotes:
                # The first standard page break after this footnote
                fn_next_page_nodes = footnote.node.xpath(
                    "following::t:pb[not(@ed)][1]",
                    namespaces=self.ROOT_NAMESPACES,
                )
                fn_next_page_node = (
                    fn_next_page_nodes[0] if fn_next_page_nodes else None
                )
                if fn_next_page_node is next_page_node:
                    page_footnotes.append(footnote)
                else:
                    # Once we reach footnotes associated with a later page, stop and return
                    break
            return page_footnotes

        # If there is no next page break, just include all following footnotes
        return list(self.all_following_footnotes)

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
            if (
                parent != self.node  # not the current pb tag
                and parent.tag == TEI_TAG.pb
                # ignore alternate edition page breaks (MEGA specific)
                and parent.get("ed") is None
                and parent == (self.next_page.node if self.next_page else None)
            ):
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

            # consolidate whitespace if it includes a newline
            # (i.e., space between indented tags in the XML)
            body_text_parts.append(re.sub(r"\s*\n\s*", "\n", text))

        return "".join(body_text_parts).strip()

    def get_footnote_contents(self) -> Generator[str]:
        """
        Generator of footnote content on this page.
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
        footnotes = self.get_page_footnotes()
        if not footnotes:
            return ""
        return "\n\n".join(str(footnote).strip() for footnote in footnotes)

    def __str__(self) -> str:
        """
        Page text contents as a string, with body text and footnotes.
        """
        return "\n\n".join(
            [self.get_body_text() or "", self.get_footnote_text() or ""]
        ).strip()


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
class TEIinput(FileInput):
    """
    Input class for TEI/XML content.  Takes a single input file,
    and yields text content by page, with page number.
    Customized for MEGA TEI/XML: follows standard edition page numbering
    and ignores pages marked as manuscript edition.
    """

    xml_doc: TEIDocument = field(init=False)
    "Parsed XML document; initialized from inherited input_file"

    field_names: ClassVar[tuple[str, ...]] = (
        *FileInput.field_names,
        "page_number",
        "section_type",
    )
    "List of field names for sentences from TEI XML input files"

    file_type = ".xml"
    "Supported file extension for TEI/XML input"

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
        Get document content as plain text.
        Generator with a dictionary of text content by page section,
        including page number and section_type ("text" or "footnote").
        Body text is yielded once per page, while each footnote is yielded individually.
        """
        # yield body text and footnotes content chunked by page with page number
        for page in self.xml_doc.pages:
            body_text = page.get_body_text()
            if body_text:
                yield {
                    "text": body_text,
                    "page_number": page.number,
                    "section_type": SectionType.TEXT.value,
                }

            for footnote_text in page.get_footnote_contents():
                yield {
                    "text": footnote_text,
                    "page_number": page.number,
                    "section_type": SectionType.FOOTNOTE.value,
                }
