"""
Functionality related to parsing ALTO XML content packaged within a zipfile,
with the goal of creating a sentence corpus with associated metadata from ALTO.
"""

import logging
from collections.abc import Generator
from dataclasses import dataclass, field
from typing import ClassVar
from zipfile import ZipFile

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

    def get_text(self) -> Generator[dict[str, str], None, None]:
        """
        Iterate over ALTO XML files contained in the zipfile to get all the text content.
        """
        self.validate_archive()

        with ZipFile(self.input_file) as archive:
            # ALTO XML filenames discovered in the zipfile
            for archive_filename in archive.namelist():
                # ignore & log non-xml files
                if not archive_filename.lower().endswith(".xml"):
                    logger.info(
                        "Ignoring non-xml file included in ALTO zipfile:  {archive_filename}"
                    )
                    continue

                # preliminary output to confirm accessing properly
                print("\n\n")
                print(archive_filename)
                with archive.open(archive_filename) as xmlfile:
                    # zipfile open returns a file-like object
                    alto_xmlobj = xmlmap.load_xmlobject_from_file(xmlfile, AltoDocument)
                    # iterate over blocks and lines as needed
                    for block in alto_xmlobj.blocks:
                        for i, line in enumerate(block.lines):
                            print(f"{i} {line}")

    def validate_archive(self) -> None:
        """
        Validate the zipfile contents: every member must be an XML file, parse
        cleanly, and declare an ALTO v4 root element. Caches the confirmed filenames
        so later `get_text` calls can skip rescanning large zipfiles.
        """

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
                    alto_xmlobj = xmlmap.load_xmlobject_from_file(xmlfile, AltoDocument)
                    print(alto_xmlobj.blocks)

            # member_filenames: list[str] = []
            # for zip_info in archive.infolist():
            #     if not zip_info.filename.lower().endswith(".xml"):
            #         raise ValueError(
            #             f"Non-XML file found in ALTO zipfile: {zip_info.filename}"
            #         )
            #     member_filenames.append(zip_info.filename)

            # if not member_filenames:
            #     raise ValueError("ALTO zipfile does not contain any XML files")

            # for member_name in member_filenames:
            #     with archive.open(member_name) as member_file:
            #         try:
            #             root = ET.parse(member_file).getroot()
            #         except ET.ParseError as exc:
            #             raise ValueError(
            #                 f"Invalid XML in ALTO zipfile member: {member_name}"
            #             ) from exc

            #     namespace, local_tag = self._split_tag(root.tag)
            #     if local_tag.lower() != "alto":
            #         raise ValueError(
            #             f"File {member_name} is not an ALTO document (root tag {root.tag})"
            #         )
            #     if namespace and namespace != self.ALTO_NAMESPACE:
            #         raise ValueError(
            #             f"Unsupported ALTO namespace in {member_name}: {namespace}"
            #         )

        # self._alto_members = sorted(member_filenames)
        # self._validated = True

    def _yield_text_for_member(
        self, archive: ZipFile, member_name: str
    ) -> Generator[dict[str, str], None, None]:
        """
        Hook for future ALTO parsing.
        """
        yield {
            "text": "",
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
