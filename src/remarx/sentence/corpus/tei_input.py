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
from timeit import default_timer as time
from typing import Any, ClassVar, NamedTuple, Self

from lxml.etree import XMLSyntaxError
from neuxml import xmlmap

from remarx.sentence.corpus.base_input import FileInput, SectionType

logger = logging.getLogger(__name__)


TEI_NAMESPACE = "http://www.tei-c.org/ns/1.0"

# namespaced tags look like {http://www.tei-c.org/ns/1.0}tagname
# create a named tuple of short tag name -> namespaced tag name
TagNames: NamedTuple = namedtuple(
    "TagNames", ("pb", "lb", "note", "add", "label", "ref", "div3", "text", "p", "hi")
)
TEI_TAG = TagNames(**{tag: f"{{{TEI_NAMESPACE}}}{tag}" for tag in TagNames._fields})
"Convenience access to namespaced TEI tag names"
INLINE_MARKUP = [TEI_TAG.hi]


class BaseTEIXmlObject(xmlmap.XmlObject):
    """
    Base class for TEI XML objects with TEI namespace included in root namespaces,
    for use in XPath expressions.
    """

    ROOT_NAMESPACES: ClassVar[dict[str, str]] = {"t": TEI_NAMESPACE}

    # TODO: omit formulas, etc.


re_normalize_whitespace = re.compile(r"\s+")


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace: replace multiple whitespace characters
    in a row with a single space.
    """
    return re_normalize_whitespace.sub(" ", text)


class TEIParagraph(BaseTEIXmlObject):
    """
    Custom :class:`neuxml.xmlmap.XmlObject` instance for a paragraph
    (or other similar text block) within a TEI XML document. (MEGA specific)
    """

    page_number = xmlmap.StringField("preceding::t:pb[not(@ed='manuscript')][1]/@n")
    continuing_page = xmlmap.StringField(".//t:pb[not(@ed='manuscript')]/@n")
    # page number within this paragraph, for paragraphs that cross page boundary

    text_nodes = xmlmap.StringListField(
        ".//text()[not(ancestor::t:label[@type='mpb']|ancestor::t:formula|ancestor::t:add|ancestor::t:table|ancestor::t:ref[@type='footnote'])]",
    )
    "list of text nodes in this paragraph; excludes manuscript edition content, formulas, tables, and footnote references"

    line_number_by_offset: dict[int, int] = None
    page_begin_offset: dict[int, int] = None

    def get_text(self) -> (str, dict[int, int]):
        """
        Generate plain text for this block of text (paragraph, etc).
        While collecting the text, build a mapping of character offsets to TEI line numbers.
        """
        text_contents: list[str] = []
        self.line_number_by_offset: dict[int, int] = {}
        self.page_begin_offset: dict[int, str] = {}
        char_offset = 0

        for el in self.text_nodes:
            # text here is an lxml smart string, which preserves context
            # in the xml tree and is associated with a parent tag.
            parent = el.getparent()
            cleaned_text = normalize_whitespace(str(el))

            # strip any leading whitespace from the first text fragment
            # to avoid including leading newlines
            if char_offset == 0:
                cleaned_text = cleaned_text.lstrip()

            # check for line begin tag; could be direct parent
            # but in cases where <lb> is immediately followed by inline markup,
            # it may be skipped due to having no tail text
            line_begin = None
            parent = el.getparent()

            if parent.tag == TEI_TAG.lb:
                line_begin = parent
            elif parent.tag in INLINE_MARKUP:
                prev = parent.getprevious()
                if prev is not None and prev.tag == TEI_TAG.lb:
                    # NOTE: currently does not support nested inline markup
                    line_begin = prev

            # record line number at the offset where it is found
            if line_begin is not None:
                line_number = int(line_begin.get("n")) if line_begin.get("n") else None
                # record character offset when line begin tag first encountered
                if (
                    line_number
                    and line_number not in self.line_number_by_offset.values()
                ):
                    self.line_number_by_offset[char_offset] = line_number

                    # ensure text separated by <lb\> has whitespace
                    # if there is a preceding text segment and it does not end
                    # with a newline, add one to the current text
                    if text_contents and not text_contents[-1].endswith(" "):
                        cleaned_text = f" {cleaned_text}"

            # if this paragraph wraps a page boundary, check for page begin
            # and store character offset
            if self.continuing_page:
                page_begin = None
                # look for parent of tail text or previous sibling of
                # line break previously identified
                if parent.tag == TEI_TAG.pb:
                    page_begin = parent
                elif line_begin is not None:
                    prev = line_begin.getprevious()
                    if prev is not None and prev.tag == TEI_TAG.pb:
                        page_begin = prev

                # if a non-manuscript edition page begin is found, store the offset
                if page_begin is not None and page_begin.get("ed") != "manuscript":
                    page_number = page_begin.get("n")
                    self.page_begin_offset[char_offset] = page_number

            # if cleaning resulted in empty string or whitespace only, omit
            if cleaned_text.strip() == "":
                continue

            text_contents.append(cleaned_text)
            char_offset += len(cleaned_text)

        # join text parts and trim trailing whitespace
        return "".join(text_contents).rstrip()


class TEIFootnote(TEIParagraph):
    """XmlObject class for footnotes, based on TEIParagraph."""

    page_number = xmlmap.StringField("preceding::t:pb[not(@ed='manuscript')][1]/@n")

    line_number = xmlmap.IntegerField("./t:lb[1]/@n")
    "Line number where this footnote begins, based on first TEI line beginning (`lb`) within this note"

    text_nodes = xmlmap.StringListField(
        ".//text()[not(ancestor::t:label[@type='mpb' or @type='footnote']|ancestor::t:formula|ancestor::t:add|ancestor::t:table)]",
    )
    # same as paragraph, but omit footnote ref and exclude label type footnote


class TEIDocument(BaseTEIXmlObject):
    """
    Custom :class:`neuxml.xmlmap.XmlObject` instance for TEI XML document.
    Customized for MEGA TEI XML.
    """

    # paragraphs, headings, or anonymous blocks other than figure captions; skip editorial intro
    text_blocks = xmlmap.NodeListField(
        "(//t:text//t:p|//t:text//t:head)[not(ancestor::t:div[@type='editorialHead'])]|//t:text//t:ab[not(ancestor::t:figure)]",
        TEIParagraph,
    )
    footnotes = xmlmap.NodeListField("//t:text//t:note[@type='footnote']", TEIFootnote)

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

        :returns: Generator with dictionaries of text content with page number and section_type ("text" or "footnote").
        """
        # yield body text and footnotes content chunked by page with page number
        start = time()
        self.text_line_numbers = {}
        self.continuing_page_numbers = {}
        total_text_blocks = 0
        for i, text_block in enumerate(self.xml_doc.text_blocks):
            para_start = time()
            text = text_block.get_text()
            if text:
                # store the line number offsets on the input class, since
                # xmlobject nodelist does NOT preserve non-xml object modifications
                self.text_line_numbers[i] = text_block.line_number_by_offset
                # for continuing pages, store offset of new page number
                if text_block.page_begin_offset:
                    self.continuing_page_numbers[i] = text_block.page_begin_offset

                yield {
                    "text": text,
                    "page_number": text_block.page_number,
                    "section_type": SectionType.TEXT.value,
                    "text_index": i,
                }
            para_elapsed_time = time() - para_start
            logger.debug(
                f"Processing page text block {i} in {para_elapsed_time:.2f} seconds"
            )
            total_text_blocks += 1

        # Yield each footnote individually to enforce separate sentence segmentation
        # so that separate footnotes cannot be combined into a single sentence
        total_footnotes = 0
        for i, footnote in enumerate(self.xml_doc.footnotes):
            fn_start = time()
            yield {
                "text": footnote.get_text(),
                "page_number": footnote.page_number,
                "section_type": SectionType.FOOTNOTE.value,
                "line_number": footnote.line_number,
            }
            # for now, we use footnote starting line number
            # for all footnote sentences, but would not be hard to adapt
            # paragraph line number logic

            fn_elapsed_time = time() - fn_start
            logger.debug(f"Processing footnote {i} in {fn_elapsed_time:.2f} seconds")
            total_footnotes += 1

        elapsed_time = time() - start
        logger.info(
            f"Processed {self.file_name} with {total_text_blocks:,} text blocks and {total_footnotes:,} footnotes in {elapsed_time:.1f} seconds"
        )

    def get_line_number(self, text_index: int, char_index: int) -> int | None:
        """
        Return the TEI line number for the specified text index and
        character index. Returns the line number at or before `char_index`;
        line number offsets must be populated by get_text().
        Returns None if line number cannot be determined.
        """
        line_number_by_offset = self.text_line_numbers[text_index]

        line_number = None
        for offset, ln in line_number_by_offset.items():
            if offset > char_index:
                break
            line_number = ln
        return line_number

    def get_extra_metadata(
        self, chunk_info: dict[str, Any], char_idx: int, sentence: str
    ) -> dict[str, Any]:
        """
        Calculate extra metadata including line number for a sentence in TEI documents
        based on the character position within the text chunk (page body or footnote).

        :returns: Dictionary with line_number for the sentence or empty dict
        """
        # If line_number is already present, no additional information is needed
        extra_info = {}
        if "line_number" in chunk_info:
            return extra_info

        # Check for text index;
        #  if available, get line number by offset within text
        i = chunk_info.get("text_index")
        if i is not None:
            extra_info["line_number"] = self.get_line_number(i, char_idx)

            # check for continuing page number
            if i in self.continuing_page_numbers:
                page_number = None
                for offset, page in self.continuing_page_numbers[i].items():
                    if offset > char_idx:
                        break
                    page_number = page
                # if found, override page number
                if page_number is not None:
                    extra_info["page_number"] = page_number

        return extra_info
