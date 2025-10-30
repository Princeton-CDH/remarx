"""
Functionality related to parsing MEGA TEI/XML content with the
goal of creating a sentence corpora with associated metadata
from the TEI.
"""

import logging
import pathlib
import re
from collections import namedtuple
from collections.abc import Generator
from dataclasses import dataclass, field
from functools import cached_property
from timeit import default_timer as time
from typing import Any, ClassVar, NamedTuple, Self

from lxml.etree import XMLSyntaxError, _Element
from neuxml import xmlmap

from remarx.sentence.corpus.base_input import FileInput, SectionType, segment_text

logger = logging.getLogger(__name__)


TEI_NAMESPACE = "http://www.tei-c.org/ns/1.0"
MATHML_NAMESPACE = "http://www.w3.org/1998/Math/MathML"  # Mathematical Markup Language (formulas in TEI)

# namespaced tags look like {http://www.tei-c.org/ns/1.0}tagname
# create a named tuple of short tag name -> namespaced tag name
TagNames: NamedTuple = namedtuple(
    "TagNames",
    (
        "pb",
        "lb",
        "note",
        "add",
        "label",
        "ref",
        "div3",
        "div",
        "div2",
        "text",
        "p",
        "ab",
        "head",
        "figure",
        "table",
    ),
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

    label = xmlmap.StringField("./t:label", normalize=True)
    "Label marker (e.g. superscript number) for this footnote."

    @property
    def text(self) -> str:
        """
        Return normalized text content for the footnote, excluding label markers and
        structural/layout descendants (tables, figures, MathML).
        """
        parts: list[str] = []
        for node in self.node.xpath(".//text()"):
            parent = node.getparent()
            if parent is None:
                continue
            if any(
                ancestor.tag == TEI_TAG.label and ancestor.get("type") == "footnote"
                for ancestor in (parent, *parent.iterancestors())
            ):
                continue
            if TEIPage.is_structural_content(parent):
                continue
            text = str(node).strip()
            if text:
                parts.append(text)
        return " ".join(parts)


@dataclass(slots=True)
class ParagraphChunk:  # is there a better name for this?
    """
    Chunk of paragraph text extracted from a TEI page. The text may not come from a
    full TEI <p> element; it may be just the slice that appears on a single page when the
    paragraph spans a page break. When `continued` is True, the remainder will appear in
    a later chunk.
    """

    element: _Element
    text: str
    line_number_map: list[tuple[int, int | None]]
    continued: bool


class TEIPage(BaseTEIXmlObject):
    """
    Custom :class:`neuxml.xmlmap.XmlObject` instance for a page
    of content within a TEI XML document.
    """

    number = xmlmap.StringField("@n")
    "page number"
    edition = xmlmap.StringField("@ed")
    "page edition, if any"

    paragraph_container_tags: ClassVar[tuple[str, ...]] = (
        TEI_TAG.p,
        TEI_TAG.ab,
        TEI_TAG.head,
    )
    structural_tags: ClassVar[tuple[str, ...]] = (
        TEI_TAG.table,
        TEI_TAG.figure,
    )
    skip_div_types: ClassVar[frozenset[str]] = frozenset({"editorialHead", "inhaltsVZ"})

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

    @staticmethod
    def is_structural_content(el: _Element) -> bool:
        """
        Determine if *el* belongs to structural (layout) content—tables, figures, MathML, or editorial wrappers.
        These blocks describe presentation rather than body prose, so we skip them when building paragraph text.
        """
        for candidate in (el, *el.iterancestors()):
            if candidate.tag in TEIPage.structural_tags:
                return True
            if candidate.tag == f"{{{MATHML_NAMESPACE}}}math":
                return True
            if candidate.tag in (TEI_TAG.div, TEI_TAG.div2, TEI_TAG.div3):
                div_type = candidate.attrib.get("type")
                if div_type in TEIPage.skip_div_types:
                    return True
        return False

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

    @classmethod
    def _paragraph_container(cls, el: _Element) -> _Element | None:
        """
        Find the closest ancestor that is treated as a paragraph container.
        """
        for candidate in (el, *el.iterancestors()):
            if candidate.tag in cls.paragraph_container_tags:
                return candidate
            if candidate.tag in (TEI_TAG.pb, TEI_TAG.text):
                break
        return None

    def iter_body_paragraphs(
        self, seen_containers: set[_Element] | None = None
    ) -> Generator[ParagraphChunk, None, None]:
        """
        Yield paragraph-level body text chunks for this page.
        """
        current_container: _Element | None = None
        paragraph_parts: list[str] = []
        line_number_map: list[tuple[int, int | None]] = []
        char_offset = 0
        last_lb_el: _Element | None = None

        def flush() -> ParagraphChunk | None:
            nonlocal \
                current_container, \
                paragraph_parts, \
                line_number_map, \
                char_offset, \
                last_lb_el
            if current_container is None:
                return None
            combined = "".join(paragraph_parts).rstrip()
            chunk: ParagraphChunk | None = None
            if combined:
                continued = bool(
                    seen_containers is not None and current_container in seen_containers
                )
                if seen_containers is not None:
                    seen_containers.add(current_container)
                chunk = ParagraphChunk(
                    element=current_container,
                    text=combined,
                    line_number_map=line_number_map.copy(),
                    continued=continued,
                )
            current_container = None
            paragraph_parts = []
            line_number_map = []
            char_offset = 0
            last_lb_el = None
            return chunk

        for text_node in self.text_nodes:
            parent = text_node.getparent()
            if parent is None:
                continue

            if self.next_page and parent == self.next_page.node:
                break

            if self.is_footnote_content(parent):
                # Skip the reference itself, but keep any punctuation/tail text that follows it.
                # Example: … "ungeheure Waarensammlung"<ref …>…</ref>, — the comma lives in ref.tail.
                if (
                    parent.tag == TEI_TAG.ref
                    and parent.get("type") == "footnote"
                    and parent.tail
                ):
                    tail_text = re.sub(r"\s*\n\s*", "\n", parent.tail).lstrip()
                    if tail_text:
                        paragraph_parts.append(tail_text)
                        char_offset += len(tail_text)
                continue

            if self.is_structural_content(parent):
                continue

            if (
                parent.tag == TEI_TAG.add
                or (parent.tag == TEI_TAG.label and parent.get("type") == "mpb")
            ) and (
                text_node.is_text or (text_node.is_tail and text_node.strip() == "")
            ):
                continue

            container = self._paragraph_container(parent)
            if container is None:
                continue

            if container != current_container:
                chunk = flush()
                if chunk:
                    yield chunk
                current_container = container

            cleaned_text = re.sub(r"\s*\n\s*", "\n", str(text_node))
            if not paragraph_parts:
                cleaned_text = cleaned_text.lstrip()

            preceding_lb: _Element | None = None
            if parent.tag == TEI_TAG.lb:
                preceding_lb = parent
            else:
                preceding_lb = self.find_preceding_lb(parent)

            if preceding_lb is not None and preceding_lb is not last_lb_el:
                line_attr = preceding_lb.get("n")
                line_number = (
                    int(line_attr) if line_attr and line_attr.isdigit() else None
                )
                line_number_map.append((char_offset, line_number))
                if paragraph_parts and not paragraph_parts[-1].endswith("\n"):
                    cleaned_text = f"\n{cleaned_text}"
                last_lb_el = preceding_lb

            if not cleaned_text:
                continue

            paragraph_parts.append(cleaned_text)
            char_offset += len(cleaned_text)

        chunk = flush()
        if chunk:
            yield chunk

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
    Custom :class:`neuxml.xmlmap.XmlObject` instance for TEI XML document.
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

    @cached_property
    def pages_by_number(self) -> dict[str, TEIPage]:
        """Dictionary lookup of standard pages by page number."""
        return {page.number: page for page in self.pages}

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
        "continued",
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
        self._seen_paragraphs: set[_Element] = set()
        self._chunk_line_maps: dict[int, tuple[tuple[int, int | None], ...]] = {}
        self._chunk_counter = 0

    def get_text(self) -> Generator[dict[str, Any]]:
        """
        Get document content as plain text. The document's content is yielded in segments
        with each segment corresponding to a dictionary containing its text content,
        page number and section type ("text" or "footnote").
        Body text is yielded once per paragraph, while each footnote is yielded individually.

        :returns: Generator with dictionaries of text content, with page number and section_type ("text" or "footnote").
        """
        start = time()
        for page in self.xml_doc.pages:
            page_start = time()

            for chunk in page.iter_body_paragraphs(self._seen_paragraphs):
                if chunk.text:
                    chunk_id = self._chunk_counter
                    self._chunk_counter += 1
                    self._chunk_line_maps[chunk_id] = chunk.line_number_map
                    yield {
                        "text": chunk.text,
                        "page_number": page.number,
                        "section_type": SectionType.TEXT.value,
                        "continued": chunk.continued,
                        "_chunk_id": chunk_id,
                    }

            # Yield each footnote individually to enforce separate sentence segmentation
            # so that separate footnotes cannot be combined into a single sentence
            for footnote in page.get_page_footnotes():
                yield {
                    "text": footnote.text,
                    "page_number": page.number,
                    "section_type": SectionType.FOOTNOTE.value,
                    "line_number": footnote.line_number,
                    "continued": False,
                }

            page_elapsed_time = time() - page_start
            logger.debug(
                f"Processing page {page.number} in {page_elapsed_time:.2f} seconds"
            )

        elapsed_time = time() - start
        logger.info(
            f"Processed {self.file_name} with {len(self.xml_doc.pages)} pages in {elapsed_time:.1f} seconds"
        )

    def get_sentences(self) -> Generator[dict[str, Any], None, None]:
        """
        Yield sentences with metadata, excluding internal bookkeeping keys.
        """
        sentence_index = 0
        for chunk_info in self.get_text():
            chunk_text = chunk_info["text"]
            for char_idx, sentence in segment_text(chunk_text):
                record: dict[str, Any] = {
                    "file": self.file_name,
                    "text": sentence,
                    "sent_index": sentence_index,
                    "sent_id": f"{self.file_name}:{sentence_index}",
                }
                for key, value in chunk_info.items():
                    if key == "text" or key.startswith("_"):
                        continue
                    record[key] = value
                record.update(self.get_extra_metadata(chunk_info, char_idx, sentence))
                yield record
                sentence_index += 1

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

        chunk_id = chunk_info.get("_chunk_id")
        if chunk_id is not None:
            line_map = self._chunk_line_maps.get(chunk_id, ())
            line_number = next(
                (ln for offset, ln in reversed(line_map) if offset <= char_idx), None
            )
            return {"line_number": line_number}

        return {"line_number": None}
