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
from typing import Any, ClassVar, NamedTuple, Self

from lxml.etree import XMLSyntaxError, _Element
from neuxml import xmlmap

from remarx.sentence.corpus.base_input import FileInput, SectionType

TEI_NAMESPACE = "http://www.tei-c.org/ns/1.0"

# namespaced tags look like {http://www.tei-c.org/ns/1.0}tagname
# create a named tuple of short tag name -> namespaced tag name
TagNames: NamedTuple = namedtuple(
    "TagNames", ("pb", "lb", "note", "add", "label", "ref", "div3", "text", "p")
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
    """XmlObject class for footnotes."""

    line_number = xmlmap.IntegerField("./t:lb[1]/@n")
    "Line number where this footnote begins, based on first TEI line beginning (`lb`) within this note"

    # use xmlmap StringField method with normalize=True to collapse whitespace in the footnote text
    text = xmlmap.StringField(".", normalize=True)
    "Normalized text content for the footnote (collapses whitespace)"


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

    def get_body_text_line_number(self, char_pos: int) -> int | None:
        """
        Return the TEI line number for the line at or before `char_pos`.
        Returns None if no line number can be determined.
        """
        if not hasattr(self, "line_number_by_offset"):
            self.get_body_text()

        # When there are no line breaks with line numbers, return None
        if not self.line_number_by_offset:
            return None

        line_number = None
        for offset, ln in self.line_number_by_offset.items():
            if offset > char_pos:
                break
            line_number = ln
        return line_number

    @staticmethod
    def find_preceding_lb(element: _Element) -> _Element | None:
        """
        Find the closest preceding <lb> element for an element.
        Needed to find the <lb/> relative to immediately following
        inline markup, e.g. <lb n="31"/><hi>text ...</hi>
        """

        # First, iterate over preceding siblings;
        # Limit to TEI nodes to avoid iterating over non-tag nodes like comments
        for sibling in element.itersiblings(f"{{{TEI_NAMESPACE}}}*", preceding=True):
            if sibling.tag == TEI_TAG.lb:
                return sibling
            # if we hit a preceding paragraph, stop iterating (beyond inline text)
            if sibling.tag == TEI_TAG.p:
                break

        # if not found, try on the parent element
        parent = element.getparent()
        # if no parent, or hit a text element, we've gone too far; bail out
        if parent is None or parent.tag == TEI_TAG.text:
            return None
        return TEIPage.find_preceding_lb(element.getparent())

    def get_body_text(self) -> str:
        """
        Extract body text content for this page, excluding footnotes and editorial content.
        While collecting the text, build a mapping of character offsets to TEI line numbers.
        """
        body_text_parts: list[str] = []
        self.line_number_by_offset: dict[int, int] = {}
        char_offset = 0

        last_lb_el = None

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

            cleaned_text = re.sub(r"\s*\n\s*", "\n", str(text))

            # Use lstrip() to strip leading whitespace from the very first text fragment
            # before concatenation to avoid counting leading newlines toward `char_offset`,
            # skewing line lookups.
            if not body_text_parts:
                cleaned_text = cleaned_text.lstrip()

            # check for line begin tag; could be direct parent
            # but in cases where <lb> is immediately followed by inline markup,
            # it may be skipped due to having no tail text
            preceding_lb = None
            if parent.tag == TEI_TAG.lb:
                preceding_lb = parent
            else:
                preceding_lb = self.find_preceding_lb(parent)

            if preceding_lb is not None and preceding_lb is not last_lb_el:
                # store the line number and character offset
                line_number = preceding_lb.get("n")
                self.line_number_by_offset[char_offset] = (
                    int(line_number) if line_number else None
                )
                # ensure text separated by <lb\> has a newline
                # if there is a preceding text segment and it does not end
                # with a newline, add one to the current text
                if body_text_parts and not body_text_parts[-1].endswith("\n"):
                    cleaned_text = f"\n{cleaned_text}"

                # set this element as the last lb handled, so we don't duplicate
                last_lb_el = preceding_lb

            if not cleaned_text:
                continue

            body_text_parts.append(cleaned_text)
            char_offset += len(cleaned_text)

        # join text parts and trim trailing whitespace
        body_text = "".join(body_text_parts).rstrip()

        return body_text

    def get_footnote_text(self) -> str:
        """
        Get all footnote content as a single string, with footnotes separated by double newlines.
        """
        return "\n\n".join(fn.text for fn in self.get_page_footnotes())

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
            # so that separate footnotes cannot be combined into a single sentence
            for footnote in page.get_page_footnotes():
                yield {
                    "text": footnote.text,
                    "page_number": page.number,
                    "section_type": SectionType.FOOTNOTE.value,
                    "line_number": footnote.line_number,
                }

    def get_extra_metadata(
        self, chunk_info: dict[str, Any], char_idx: int, sentence: str
    ) -> dict[str, Any]:
        """
        Calculate extra metadata including line number for a sentence in TEI documents
        based on the character position within the text chunk (page body or footnote).

        :returns: Dictionary with line_number for the sentence (None if not found)
        """
        # If line_number is already in chunk_info (e.g., for footnotes), use it directly
        if "line_number" in chunk_info:
            return {"line_number": chunk_info["line_number"]}

        # Otherwise, calculate it for body text based on character position
        page_number = chunk_info["page_number"]
        page = next((p for p in self.xml_doc.pages if p.number == page_number), None)

        if page:
            line_number = page.get_body_text_line_number(char_idx)
            return {"line_number": line_number}

        return {"line_number": None}
