"""
Functionality related to parsing ALTO XML content packaged within a zipfile,
with the goal of creating a sentence corpus with associated metadata from ALTO.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from collections.abc import Generator
from dataclasses import dataclass, field
from typing import ClassVar
from zipfile import ZipFile

from remarx.sentence.corpus.base_input import FileInput, SectionType


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

        with ZipFile(self.input_file):
            for member_name in self._alto_members:
                print(f"Processing ALTO XML file: {member_name}")

                # Yield stub metadata for each ALTO XML; actual text extraction forthcoming.
                yield {
                    "text": "",
                    "section_type": SectionType.TEXT.value,
                }

    def validate_archive(self) -> None:
        """
        Validate the zipfile contents: every member must be an XML file, parse
        cleanly, and declare an ALTO v4 root element. Caches the confirmed filenames
        so later `get_text` calls can skip rescanning large zipfiles.
        """
        if self._validated:
            return

        with ZipFile(self.input_file) as archive:
            member_names: list[str] = []
            for zip_info in archive.infolist():
                if zip_info.is_dir():
                    continue
                if not zip_info.filename.lower().endswith(".xml"):
                    raise ValueError(
                        f"Non-XML file found in ALTO zipfile: {zip_info.filename}"
                    )
                member_names.append(zip_info.filename)

            if not member_names:
                raise ValueError("ALTO zipfile does not contain any XML files")

            for member_name in member_names:
                with archive.open(member_name) as member_file:
                    try:
                        root = ET.parse(member_file).getroot()
                    except ET.ParseError as exc:
                        raise ValueError(
                            f"Invalid XML in ALTO zipfile member: {member_name}"
                        ) from exc

                namespace, local_tag = self._split_tag(root.tag)
                if local_tag.lower() != "alto":
                    raise ValueError(
                        f"File {member_name} is not an ALTO document (root tag {root.tag})"
                    )
                if namespace and namespace != self.ALTO_NAMESPACE:
                    raise ValueError(
                        f"Unsupported ALTO namespace in {member_name}: {namespace}"
                    )

        self._alto_members = sorted(member_names)
        self._validated = True

    @staticmethod
    def _split_tag(tag: str) -> tuple[str | None, str]:
        """
        Split a potentially namespaced XML tag into (namespace, local_tag).
        """
        if tag.startswith("{"):
            namespace, _, local = tag[1:].partition("}")
            return namespace, local
        return None, tag
