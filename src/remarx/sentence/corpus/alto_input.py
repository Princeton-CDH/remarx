"""
Functionality related to parsing ALTO XML content packaged within a zipfile,
with the goal of creating a sentence corpus with associated metadata from ALTO.
"""

import logging
from collections.abc import Generator
from dataclasses import dataclass, field
from typing import ClassVar
from zipfile import ZipFile

from lxml.etree import XMLSyntaxError
from neuxml import xmlmap

from remarx.sentence.corpus.base_input import FileInput, SectionType

logger = logging.getLogger(__name__)


class AltoXmlObject(xmlmap.XmlObject):
    """
    Base :class:`neuxml.xmlmap.XmlObject` class for ALTO-XML content.
    """

    # alto namespace v4; we may eventually need to support other versions
    ROOT_NAMESPACES: ClassVar[dict[str, str]] = {
        "alto": "http://www.loc.gov/standards/alto/ns-v4#"
    }


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


class AltoDocument(AltoXmlObject):
    """
    :class:`neuxml.xmlmap.XmlObject` instance for a single ALTO XML file
    """

    blocks = xmlmap.NodeListField(".//alto:TextBlock", TextBlock)


@dataclass
class ALTOInput(FileInput):
    """
    Preliminary FileInput implementation for ALTO XML delivered as a zipfile.
    Iterates through ALTO XML members and stubs out chunk yielding for future parsing.
    """

    ALTO_NAMESPACE: ClassVar[str] = "http://www.loc.gov/standards/alto/ns-v4#"

    field_names: ClassVar[tuple[str, ...]] = (*FileInput.field_names, "section_type")
    "List of field names for sentences originating from ALTO XML content."

    file_type: ClassVar[str] = ".zip"
    "Supported file extension for ALTO zipfiles."

    _validated: bool = field(init=False, default=False)
    "Flag indicating whether the input archive has already been validated."

    _alto_members: list[str] = field(init=False, default_factory=list)
    """Sorted list of ALTO XML filenames discovered during validation."""

    _chunk_cache: dict[str, list[dict[str, str]]] = field(
        init=False, default_factory=dict
    )
    """Cached chunk data for validated ALTO XML members."""

    def get_text(self) -> Generator[dict[str, str], None, None]:
        """
        Iterate over ALTO XML files contained in the zipfile to get all the text content.
        """
        self.validate_archive()

        for member_name in self._alto_members:
            logger.info("Processing ALTO XML file: %s", member_name)
            yield from self._chunk_cache.get(member_name, [])

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
                    except XMLSyntaxError as err:
                        logger.warning(
                            "Skipping ALTO zipfile member with invalid XML: %s",
                            archive_filename,
                        )
                        logger.debug("Invalid XML error", exc_info=err)
                        continue

                namespace, local_tag = self._split_tag(alto_xmlobj.node.tag)
                if local_tag.lower() != "alto":
                    logger.warning(
                        "Skipping non-ALTO XML file in zip: %s (root tag %s)",
                        archive_filename,
                        alto_xmlobj.node.tag,
                    )
                    continue
                if namespace and namespace != self.ALTO_NAMESPACE:
                    logger.warning(
                        "Skipping ALTO XML file with unsupported namespace in %s: %s",
                        archive_filename,
                        namespace,
                    )
                    continue

                chunks = list(self._yield_text_for_document(alto_xmlobj))
                member_filenames.append(archive_filename)
                chunk_cache[archive_filename] = chunks

        if not member_filenames:
            raise ValueError("ALTO zipfile does not contain any valid ALTO XML files")

        self._alto_members = sorted(member_filenames)
        self._chunk_cache = chunk_cache
        self._validated = True

    def _yield_text_for_document(
        self, alto_doc: AltoDocument
    ) -> Generator[dict[str, str], None, None]:
        """
        Hook for future ALTO parsing.
        """
        lines: list[str] = []
        for block in alto_doc.blocks:
            lines.extend(line.text_content for line in block.lines if line.text_content)

        yield {
            "text": "\n".join(lines),
            "section_type": SectionType.TEXT.value,
        }

    @staticmethod
    def _split_tag(tag: str) -> tuple[str | None, str]:
        """
        Split a potentially namespaced XML tag into (namespace, local_tag).
        """
        if tag.startswith("{"):
            namespace, _, local = tag[1:].partition("}")
            return namespace, local
        return None, tag
