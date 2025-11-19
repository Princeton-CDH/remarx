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

                # pre-compute metadata to apply to each block so that it can be merged
                # as we iterate and while footnotes are buffered
                metadata_by_block = self._collect_article_metadata(alto_xmlobj)
                footnote_chunks: list[dict[str, str]] = []

                for idx, block in enumerate(alto_xmlobj.sorted_blocks):
                    section = alto_xmlobj.tags.get(block.tag_id, SectionType.TEXT.value)
                    block_text = block.text_content
                    chunk = {
                        "text": block_text,
                        "section_type": section,
                        "file": base_filename,  # use the base xml file for consistency
                    } | metadata_by_block.get(idx, {"title": "", "author": ""})

                    # Apply section filtering up front
                    if include_sections is not None and section not in include_sections:
                        continue

                    # Buffer footnotes so they are emitted after the body text
                    if section == "footnote":
                        footnote_chunks.append(chunk)
                        continue

                    yield chunk

                # Emit buffered footnotes at the end
                yield from footnote_chunks

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

    def _collect_article_metadata(
        self, alto_xmlobj: AltoDocument
    ) -> dict[int, dict[str, str]]:
        """
        Collect title/author metadata once per page and return a mapping of block
        index -> metadata to merge into emitted chunks. Title/author blocks are
        concatenated when consecutive so that multi-line headings/authors are preserved.

        Doing this up front avoids fragile per-block state and supports buffering
        footnotes (which still need the correct article metadata) before yielding.
        """
        current_title = ""
        current_author = ""
        metadata_by_block: dict[int, dict[str, str]] = {}
        blocks = alto_xmlobj.sorted_blocks

        def get_section(block: TextBlock) -> str:
            return alto_xmlobj.tags.get(block.tag_id) or SectionType.TEXT.value

        i = 0
        while i < len(blocks):
            section = get_section(blocks[i])

            if section == "Title":
                # accumulate consecutive title blocks to preserve multi-line headings
                title_lines: list[str] = []
                j = i
                while j < len(blocks) and get_section(blocks[j]) == "Title":
                    text_clean = (blocks[j].text_content or "").strip()
                    if text_clean:
                        title_lines.append(text_clean)
                    j += 1
                current_title = "\n".join(title_lines)
                # new title resets author context
                current_author = ""
                # apply the updated metadata to all title blocks in this run
                for k in range(i, j):
                    metadata_by_block[k] = {
                        "title": current_title,
                        "author": current_author,
                    }
                i = j
                continue

            if section == "author":
                # accumulate consecutive author blocks
                author_lines: list[str] = []
                j = i
                while j < len(blocks) and get_section(blocks[j]) == "author":
                    text_clean = (blocks[j].text_content or "").strip()
                    if text_clean:
                        author_lines.append(text_clean)
                    j += 1
                current_author = "\n".join(author_lines)
                for k in range(i, j):
                    metadata_by_block[k] = {
                        "title": current_title,
                        "author": current_author,
                    }
                i = j
                continue

            # For any other section, apply the current running metadata
            metadata_by_block[i] = {"title": current_title, "author": current_author}
            i += 1

        return metadata_by_block
