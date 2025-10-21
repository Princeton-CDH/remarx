"""
Functionality related to parsing ALTO XML content packaged within a zipfile,
with the goal of creating a sentence corpus with associated metadata from ALTO.
"""

import logging
import pathlib
from collections.abc import Generator
from dataclasses import dataclass
from functools import cached_property
from typing import ClassVar
from zipfile import ZipFile

from lxml import etree
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

    def text_chunks(self) -> Generator[dict[str, str]]:
        """
        Returns a generator of a dictionary of text content and section type,
        one dictionary per text block on the page.
        """
        # yield by block, since in future we may set section type
        # based on block-level semantic tagging
        for block in self.sorted_blocks:
            yield {"text": block.text_content, "section_type": SectionType.TEXT.value}


@dataclass
class ALTOInput(FileInput):
    """
    Preliminary FileInput implementation for ALTO XML delivered as a zipfile.
    Iterates through ALTO XML members and stubs out chunk yielding for future parsing.
    """

    field_names: ClassVar[tuple[str, ...]] = (*FileInput.field_names, "section_type")
    "List of field names for sentences originating from ALTO XML content."

    file_type: ClassVar[str] = ".zip"
    "Supported file extension for ALTO zipfiles (.zip)"

    def get_text(self) -> Generator[dict[str, str], None, None]:
        """
        Iterate over ALTO XML files contained in the zipfile and return
        a generator of text content.
        """
        num_valid_files = 0
        with ZipFile(self.input_file) as archive:
            # iterate over all files in the zipfile; use infolist to get in order
            for file_zipinfo in archive.infolist():
                zip_filepath = file_zipinfo.filename
                base_filename = pathlib.Path(zip_filepath).name
                # ignore & log non-xml files
                if not base_filename.lower().endswith(".xml"):
                    logger.info(
                        f"Ignoring non-xml file included in ALTO zipfile: {zip_filepath}"
                    )
                    continue
                # if the file is .xml, attempt to open as an ALTO XML
                with archive.open(zip_filepath) as xmlfile:
                    logger.info(f"Processing XML file {zip_filepath}")
                    # zipfile archive open returns a file-like object
                    try:
                        alto_xmlobj = xmlmap.load_xmlobject_from_file(
                            xmlfile, AltoDocument
                        )
                    except etree.XMLSyntaxError as err:
                        logger.warning(f"Skipping {zip_filepath} : invalid XML")
                        logger.debug(f"XML syntax error: {err}", exc_info=err)
                        continue

                if not alto_xmlobj.is_alto():
                    # TODO: add unit test for this case
                    logger.warning(
                        f"Skipping non-ALTO XML file {zip_filepath} (root element {alto_xmlobj.node.tag})"
                    )
                    continue

                num_valid_files += 1
                # report total # blocks, lines for each file as processed
                logger.info(
                    f"{base_filename}: {len(alto_xmlobj.blocks)} blocks, {len(alto_xmlobj.lines)} lines"
                )
                # use the xml file as filename here, rather than zipfile for all
                for chunk in alto_xmlobj.text_chunks():
                    yield chunk | {"file": base_filename}

                # TODO: where to report / how to check no content?
                # is this a real problem?

        # error if no valid files were found
        if num_valid_files == 0:
            raise ValueError(f"No valid ALTO XML files found in {self.input_file}")
