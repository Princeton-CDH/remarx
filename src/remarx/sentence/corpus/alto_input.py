"""
Functionality related to parsing ALTO XML content packaged within a zipfile,
with the goal of creating a sentence corpus with associated metadata from ALTO.
"""

import logging
import pathlib
from collections.abc import Generator
from dataclasses import dataclass
from functools import cached_property
from timeit import default_timer as time
from typing import ClassVar
from zipfile import ZipFile, ZipInfo

from lxml import etree
from natsort import natsorted
from neuxml import xmlmap

from remarx.sentence.corpus.base_input import FileInput, SectionType

logger = logging.getLogger(__name__)


ALTO_NAMESPACE_V4: str = "http://www.loc.gov/standards/alto/ns-v4#"


class AltoXmlObject(xmlmap.XmlObject):
    """
    Base :class:`neuxml.xmlmap.XmlObject` class for ALTO-XML content.
    """

    # alto namespace v4; we may eventually need to support other versions
    ROOT_NAMESPACES: ClassVar[dict[str, str]] = {"alto": ALTO_NAMESPACE_V4}


class AltoTag(AltoXmlObject):
    """
    Class to for Alto tags. Used to map tag id to tag label.
    """

    id = xmlmap.StringField("@ID")
    "tag id (`@ID` attribute)"
    label = xmlmap.StringField("@LABEL")
    "tag label (`@LABEL` attribute)"


class AltoBlock(AltoXmlObject):
    """
    Base class for an ALTO element with position information.
    """

    vertical_position = xmlmap.FloatField("@VPOS")
    horizontal_position = xmlmap.FloatField("@HPOS")


class TextLine(AltoBlock):
    """
    Single line of text (`TextLine`) in an ALTO document
    """

    text_content = xmlmap.StringField("alto:String/@CONTENT")

    def __str__(self) -> str:
        """
        Override default string method to return text content of this line.
        """
        return self.text_content


class TextBlock(AltoBlock):
    """
    Block of text with one or more lines.
    """

    lines = xmlmap.NodeListField("alto:TextLine", TextLine)
    tag_id = xmlmap.StringField("@TAGREFS")

    @cached_property
    def sorted_lines(self) -> list[TextLine]:
        """
        Returns a list of TextLines for this block, sorted by vertical position.
        """
        # there's no guarantee that xml document order follows page order,
        # so sort by @VPOS (may need further refinement for more complicated layouts)
        return sorted(self.lines, key=lambda line: line.vertical_position)

    @property
    def text_content(self) -> str:
        """
        Text contents of this block; newline-delimited content of
        each line within this block, sorted by vertical position.
        """
        return "\n".join([line.text_content for line in self.sorted_lines])


class AltoDocument(AltoXmlObject):
    """
    :class:`neuxml.xmlmap.XmlObject` instance for a single ALTO XML file
    """

    blocks = xmlmap.NodeListField(".//alto:TextBlock", TextBlock)
    lines = xmlmap.NodeListField(".//alto:TextLine", TextLine)
    _tags = xmlmap.NodeListField("alto:Tags/alto:OtherTag", AltoTag)

    def is_alto(self) -> bool:
        """
        Check if this is an ALTO-XML document, based on the root element
        """
        # parse with QName to access namespace and tag name without namespace
        root_element = etree.QName(self.node.tag)
        # both must match
        return (
            root_element.namespace == ALTO_NAMESPACE_V4
            and root_element.localname == "alto"
        )

    @cached_property
    def tags(self) -> dict[str, str]:
        """
        Dictionary of block-level tags; key is id, value is label.
        """
        return {tag.id: tag.label for tag in self._tags}

    @property
    def sorted_blocks(self) -> list[TextBlock]:
        """
        Returns a list of TextBlocks for this page, sorted by vertical position.
        """
        # there's no guarantee that xml document order follows page order,
        # so sort by @VPOS (may need further refinement for more complicated layouts).
        # NOTE: in some cases, a textblock may not have a VPOS attribute;
        # in that case, use the position for the first line
        # (text block id = eSc_dummyblock_, but appears to have real content)
        # if block has no line, sort text block last
        if not self.blocks:
            return []
        return sorted(
            self.blocks,
            key=lambda block: block.vertical_position
            or (
                block.sorted_lines[0].vertical_position if block.lines else float("inf")
            ),
        )

    def text_chunks(self, include: set[str] | None = None) -> Generator[dict[str, str]]:
        """
        Returns a generator of a dictionary of text content and section type,
        one dictionary per text block on the page.
        """
        # yield by block, since in future we may set section type
        # based on block-level semantic tagging
        for block in self.sorted_blocks:
            # use tag for section type, if set; if unset, assume text
            section = self.tags.get(block.tag_id) or SectionType.TEXT.value
            # if include list is specified and section is not in it, skip;
            # currently includes if section type is unset
            if include is not None and section is not None and section not in include:
                continue
            yield {"text": block.text_content, "section_type": section}


@dataclass
class ALTOInput(FileInput):
    """
    FileInput implementation for ALTO XML delivered as a zipfile.
    Iterates through ALTO XML members and yields text blocks with ALTO metadata.
    """

    field_names: ClassVar[tuple[str, ...]] = (
        *FileInput.field_names,
        "section_type",
        "title",
        "author",
    )
    "List of field names for sentences originating from ALTO XML content."

    file_type: ClassVar[str] = ".zip"
    "Supported file extension for ALTO zipfiles (.zip)"

    default_include: ClassVar[set[str]] = {"text", "footnote", "Title"}
    "Default content sections to include"

    filter_sections: bool = True
    "Whether to filter text sections by block type"
    # do we need a way to specify custom includes?

    def get_text(self) -> Generator[dict[str, str], None, None]:
        """
        Iterate over ALTO XML files contained in the zipfile and return
        a generator of text content.
        """
        num_files = 0
        num_valid_files = 0
        include_sections = self.default_include if self.filter_sections else None

        # track article metadata across pages; metadata is updated while iterating
        # through blocks and reused for footnotes or later sentences. The
        # _collecting_title/_collecting_author flags record cases where consecutive
        # blocks on the same page contribute to a single field (common in DNZ,
        # where titles or author lines are split across multiple TextBlocks).
        self._current_title = ""
        self._current_author = ""
        self._collecting_title = False
        self._collecting_author = False
        # set when we encounter a blank title block; cleared once we know whether
        # the blank block marked the start of a new article
        self._pending_title_reset = False

        start = time()
        with ZipFile(self.input_file) as archive:
            # iterate over all files in the zipfile;
            # use natural sorting to process in logical order
            for zip_filepath in natsorted(archive.namelist()):
                num_files += 1
                # check for non-xml/non alto / invalid files
                alto_xmlobj = self.check_zipfile_path(zip_filepath, archive)
                if alto_xmlobj is None:
                    continue
                # get base filename for logging and file name in metadata
                base_filename = pathlib.Path(zip_filepath).name
                num_valid_files += 1
                # report total # blocks, lines for each file as processed
                logger.debug(
                    f"{base_filename}: {len(alto_xmlobj.blocks)} blocks, {len(alto_xmlobj.lines)} lines"
                )

                # ensure block-level continuation state resets between files
                self._collecting_title = False
                self._collecting_author = False
                self._pending_title_reset = False

                for block in alto_xmlobj.sorted_blocks:
                    section = alto_xmlobj.tags.get(block.tag_id, SectionType.TEXT.value)
                    block_text = block.text_content
                    self._update_article_metadata(section, block_text)

                    if include_sections is None or section in include_sections:
                        yield {
                            "text": block_text,
                            "section_type": section,
                            "title": self._current_title,
                            "author": self._current_author,
                            # use the base xml file as filename here, rather than zipfile for all
                            "file": base_filename,
                        }

        elapsed_time = time() - start
        logger.info(
            f"Processed {self.file_name} with {num_files} files ({num_valid_files} valid ALTO) in {elapsed_time:.1f} seconds"
        )

        # error if no valid files were found
        if num_valid_files == 0:
            raise ValueError(f"No valid ALTO XML files found in {self.file_name}")

    def check_zipfile_path(
        self, zip_filepath: ZipInfo, zip_archive: ZipFile
    ) -> None | AltoDocument:
        """
        Check an individual file included in the zip archive to determine if
        parsing should be attempted and if it is a valid ALTO XML file. Returns
        AltoDocument if valid, otherwise None.
        """
        base_filename = pathlib.Path(zip_filepath).name
        # ignore & log non-xml files
        if not base_filename.lower().endswith(".xml"):
            logger.info(
                f"Ignoring non-xml file included in ALTO zipfile: {zip_filepath}"
            )
            return

        # if the file is .xml, attempt to open as an ALTO XML
        with zip_archive.open(zip_filepath) as xmlfile:
            logger.info(f"Processing XML file {zip_filepath}")
            # zipfile archive open returns a file-like object
            try:
                alto_xmlobj = xmlmap.load_xmlobject_from_file(xmlfile, AltoDocument)
            except etree.XMLSyntaxError as err:
                logger.warning(f"Skipping {zip_filepath} : invalid XML")
                logger.debug(f"XML syntax error: {err}", exc_info=err)
                return

        if not alto_xmlobj.is_alto():
            # TODO: add unit test for this case
            logger.warning(
                f"Skipping non-ALTO XML file {zip_filepath} (root element {alto_xmlobj.node.tag})"
            )
            return

        # if there are no text lines, no processing is needed (but warn)
        if len(alto_xmlobj.lines) == 0:
            logger.warning(f"No text lines in ALTO XML file: {base_filename}")
            return

        return alto_xmlobj

    def _update_article_metadata(
        self, section: str | None, block_text: str | None
    ) -> None:
        """
        Update running title and author metadata based on the current block label.

        NOTE: Some DNZ articles include trailing signatures or initials without
        ALTO author tags; those cases are not yet supported since there is no
        structured signal to retroactively update metadata for prior text blocks.
        TODO: capture trailing author initials when the ALTO tagging provides a reliable signal.
        """
        # Examples of unsupported trailing author cases:
        # - text block ending with "Oskar Geck." on 1896-97a.pdf_page_124.xml
        # - closing "Dr. B." line on 1896-97a.pdf_page_253.xml

        section = section or SectionType.TEXT.value
        text_clean = (block_text or "").strip()

        if section == "Title":
            self._collecting_author = False

            if text_clean:
                if self._pending_title_reset:
                    self._reset_article_metadata()
                    self._pending_title_reset = False

                if self._collecting_title and self._current_title:
                    self._current_title = f"{self._current_title}\n{text_clean}"
                else:
                    # start a new title; reset author since author metadata follows title
                    self._current_title = text_clean
                    self._current_author = ""
                self._collecting_title = True
            else:
                # blank title blocks indicate the start of a new article unless the
                # following block provides author metadata
                self._collecting_title = False
                self._pending_title_reset = True
            return

        if section == "author":
            self._collecting_title = False
            # author blocks finalize title aggregation; metadata now applies to body/footnotes

            if self._pending_title_reset:
                # blank title immediately followed by author indicates the metadata
                # belongs to the existing article; do not reset
                self._pending_title_reset = False

            if text_clean:
                if self._collecting_author and self._current_author:
                    self._current_author = f"{self._current_author}\n{text_clean}"
                else:
                    self._current_author = text_clean
                self._collecting_author = True
            else:
                # blank author blocks indicate lack of author metadata for this article
                self._current_author = ""
                self._collecting_author = False

            return

        # any other section: conclude any title/author collection and apply pending resets
        if self._pending_title_reset:
            self._reset_article_metadata()
            self._pending_title_reset = False

        self._collecting_title = False
        self._collecting_author = False

    def _reset_article_metadata(self) -> None:
        """
        Clear currently collected title/author metadata when a new article boundary is detected.
        """
        self._current_title = ""
        self._current_author = ""
