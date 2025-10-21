"""
Functionality related to parsing ALTO XML content packaged within a zipfile,
with the goal of creating a sentence corpus with associated metadata from ALTO.
"""

import logging
from collections.abc import Generator
from dataclasses import dataclass
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

    @property
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
        # so sort by @VPOS (may need further refinement for more complicated layouts)
        return sorted(self.blocks, key=lambda block: block.vertical_position)

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
        # TODO: we need to associate text content with the
        # page file name within the archive, not the zipfile name
        with ZipFile(self.input_file) as archive:
            # iterate over all files in the zipfile, in order
            for filename in archive.namelist():
                # ignore & log non-xml files
                if not filename.lower().endswith(".xml"):
                    logger.info(
                        f"Ignoring non-xml file included in ALTO zipfile: {filename}"
                    )
                    continue
                # if the file is .xml, attempt to open as an ALTO XML
                with archive.open(filename) as xmlfile:
                    # zipfile archive open returns a file-like object
                    try:
                        alto_xmlobj = xmlmap.load_xmlobject_from_file(
                            xmlfile, AltoDocument
                        )
                    except etree.XMLSyntaxError as err:
                        logger.warning(f"Skipping XML file {filename} : invalid XML")
                        logger.debug("Invalid XML error", exc_info=err)
                        continue

                if not alto_xmlobj.is_alto():
                    # TODO: add unit test for this case
                    logger.warning(
                        f"Skipping non-ALTO XML file {filename} (root element {alto_xmlobj.node.tag})"
                    )
                    continue

                # TODO: patch in xml filename here
                yield from alto_xmlobj.text_chunks
                # TODO: where to report / how to check no content?

    def validate_archive(self) -> None:
        """
        Validate the zipfile contents: every member must be an XML file, parse
        cleanly, and declare an ALTO v4 root element. Caches the confirmed filenames
        so later `get_text` calls can skip rescanning large zipfiles.
        """

        if self._validated:
            return

        member_filenames: list[str] = []
        chunk_cache: dict[str, list[dict[str, str]]] = {}

        with ZipFile(self.input_file) as archive:
            # ALTO XML filenames discovered in the zipfile
            for archive_filename in archive.namelist():
                # ignore & log non-xml files
                if not archive_filename.lower().endswith(".xml"):
                    logger.info(
                        "Ignoring non-xml file included in ALTO zipfile:  {archive_filename}"
                    )
                    continue

                with archive.open(archive_filename) as xmlfile:
                    try:
                        alto_xmlobj = xmlmap.load_xmlobject_from_file(
                            xmlfile, AltoDocument
                        )
                    except etree.XMLSyntaxError as err:
                        logger.warning(
                            "Skipping ALTO file %s : invalid XML",
                            archive_filename,
                        )
                        logger.debug("Invalid XML error", exc_info=err)
                        continue

                if not alto_xmlobj.is_alto():
                    # TODO: add unit test for this case
                    logger.warning(
                        "Skipping non-ALTO XML file %s (root element %s)",
                        archive_filename,
                        alto_xmlobj.node.tag,
                    )
                    continue

                chunks = list(
                    self._yield_text_for_document(alto_xmlobj, archive_filename)
                )
                member_filenames.append(archive_filename)
                chunk_cache[archive_filename] = chunks

        if not member_filenames:
            raise ValueError("ALTO zipfile does not contain any valid ALTO XML files")

        self._alto_members = sorted(member_filenames)
        self._chunk_cache = chunk_cache
        self._validated = True

    def _yield_text_for_document(
        self, alto_doc: AltoDocument, member_name: str
    ) -> Generator[dict[str, str], None, None]:
        """
        Hook for future ALTO parsing.
        """

        def sort_key(block_or_line: AltoBlock) -> float:
            horizontal_position = block_or_line.horizontal_position
            return float("inf") if horizontal_position is None else horizontal_position

        sorted_blocks = sorted(alto_doc.blocks, key=sort_key)

        lines: list[str] = []
        for block in sorted_blocks:
            sorted_lines = sorted(block.lines, key=sort_key)
            lines.extend(
                line.text_content for line in sorted_lines if line.text_content
            )

        if not lines:
            logger.warning("No text content found in ALTO XML file: %s", member_name)

        yield {
            "text": "\n".join(lines),
            "section_type": SectionType.TEXT.value,
        }
