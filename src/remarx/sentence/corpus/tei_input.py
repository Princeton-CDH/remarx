"""
Functionality related to parsing MEGA TEI/XML content with the
goal of creating a sentence corpora with associated metadata
from the TEI.
"""

import pathlib
import re
from collections import OrderedDict, namedtuple
from collections.abc import Generator
from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, ClassVar, NamedTuple, Self

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


class TEIFootnote(BaseTEIXmlObject):
    """XmlObject wrapper for footnotes with convenience accessors."""

    first_line_break = xmlmap.StringField("(.//t:lb[@n])[1]/@n")
    "Line number of the first TEI line break (`lb`) within this footnote"

    def get_first_line_number(self) -> int:
        """Return the first line number for this footnote."""
        return int(self.first_line_break)

    def get_text(self) -> str:
        """Return cleaned text content for the footnote."""
        # Split on newlines and strip each line, then join with spaces
        text = " ".join(
            line.strip() for line in "".join(self.node.itertext()).splitlines()
        )
        return " ".join(text.split())


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
        "following::t:note[@type='footnote']", TEIFootnote
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

    def get_page_footnotes(self) -> list[TEIFootnote]:
        """
        Filters footnotes to keep only the footnotes that belong to this page.
        Only includes footnotes that occur between this pb and the next standard pb[not(@ed)].
        """
        page_footnotes: list[TEIFootnote] = []

        for footnote in self.following_footnotes:
            # If we have a next page and this footnote belongs to it, we're done
            if self.next_page and footnote in self.next_page.following_footnotes:
                break
            page_footnotes.append(footnote)

        return page_footnotes

    def get_body_text_line_number(self, char_pos: int) -> int:
        """
        Return the TEI line number for the line preceding ``char_pos``.
        """
        if char_pos < 0:
            char_pos = 0

        if not hasattr(self, "_line_index_by_offset"):
            self.get_body_text()

        line_index: OrderedDict[int, int] = getattr(
            self, "_line_index_by_offset", OrderedDict()
        )
        offsets: list[int] = getattr(self, "_sorted_line_offsets", [])

        if not offsets:
            return 1

        line_number = line_index[offsets[0]]
        for offset in offsets:
            if offset > char_pos:
                break
            line_number = line_index[offset]
        return line_number

    def get_body_text(self) -> str:
        """
        Extract body text content for this page, excluding footnotes and editorial content.
        While collecting the text, build an index of character offsets to TEI line numbers.
        """
        body_text_parts: list[str] = []
        line_index: OrderedDict[int, int] = OrderedDict()
        offsets: list[int] = []
        char_offset = 0

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

            raw_fragment = str(text)
            cleaned_fragment = re.sub(r"\s*\n\s*", "\n", raw_fragment)
            if not body_text_parts:
                cleaned_fragment = cleaned_fragment.lstrip()

            if not cleaned_fragment:
                continue

            if parent.tag == TEI_TAG.lb:
                line_number_attr = parent.get("n")
                if line_number_attr:
                    line_number = int(line_number_attr)
                    if char_offset not in line_index:
                        line_index[char_offset] = line_number
                        offsets.append(char_offset)

            body_text_parts.append(cleaned_fragment)
            char_offset += len(cleaned_fragment)

        # join fragments and trim trailing whitespace to mirror prior normalization
        body_text = "".join(body_text_parts).rstrip()

        self._line_index_by_offset = line_index
        self._sorted_line_offsets = offsets

        return body_text

    def get_individual_footnotes(self) -> Generator[str]:
        """
        Get individual footnote content as a generator.
        Yields each footnote's text content individually as a separate string element.
        Each yielded element corresponds to one complete footnote from the page.
        """
        self._footnote_line_number_map: dict[int, int] = {}

        for footnote in self.get_page_footnotes():
            footnote_text = footnote.get_text()
            line_number = footnote.get_first_line_number() or 1

            self._footnote_line_number_map[id(footnote_text)] = line_number
            yield footnote_text

    def get_footnote_line_number(self, footnote_text: str) -> int:
        """
        Return the first TEI line number recorded for the provided footnote text.
        """
        line_number = getattr(self, "_footnote_line_number_map", {}).get(
            id(footnote_text)
        )
        if line_number is not None:
            return line_number
        return 1

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
        "line_number",
    )
    "List of field names for sentences from TEI XML input files"

    file_type = ".xml"
    "Supported file extension for TEI/XML input"

    def __post_init__(self) -> None:
        """
        After default initialization, parse the input file as a
         [TEIDocument][remarx.sentence.corpus.tei_input.TEIDocument]
        and store it as [xml_doc][remarx.sentence.corpus.tei_input.TEIinput.xml_doc].
        """
        # parse the input file as xml and save the result
        self.xml_doc = TEIDocument.init_from_file(self.input_file)

    def get_text(self) -> Generator[dict[str, str]]:
        """
        Get document content as plain text. The document's content is yielded in segments
        with each segment corresponding to a dictionary of containing its text content,
        page number and section type ("text" or "footnote").
        Body text is yielded once per page, while each footnote is yielded individually.

        :returns: Generator with dictionaries of text content, with page number and section_type ("text" or "footnote").
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

            # Yield each footnote individually to enforce separate sentence segmentation
            # so that separate footnotes cannot be combined into a single sentence by segmentation.
            for footnote_text in page.get_individual_footnotes():
                yield {
                    "text": footnote_text,
                    "page_number": page.number,
                    "section_type": SectionType.FOOTNOTE.value,
                }

    def get_extra_metadata(
        self, chunk_info: dict[str, Any], char_idx: int, sentence: str
    ) -> dict[str, Any]:
        """
        Calculate extra metadata including line number for a sentence in TEI documents
        based on the character position within the text chunk (page body or footnote).

        :returns: Dictionary with line_number (1-indexed) for the sentence
        """
        page_number = chunk_info["page_number"]
        section_type = chunk_info["section_type"]

        # Find the corresponding page object to calculate line numbers
        page = next((p for p in self.xml_doc.pages if p.number == page_number), None)
        if page is None:
            return {"line_number": 1}

        if section_type == SectionType.FOOTNOTE.value:
            line_number = page.get_footnote_line_number(chunk_info["text"])
        else:
            line_number = page.get_body_text_line_number(char_idx)

        return {"line_number": line_number}
