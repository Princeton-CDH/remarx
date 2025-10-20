import logging
import shutil
from pathlib import Path
from zipfile import ZipFile

import pytest
from neuxml import xmlmap

from remarx.sentence.corpus.alto_input import AltoDocument, ALTOInput
from remarx.sentence.corpus.base_input import FileInput, SectionType


@pytest.fixture
def alto_sample_zip(tmp_path: Path) -> Path:
    fixtures_dir = Path(__file__).parent / "fixtures"
    source_zip = fixtures_dir / "alto_sample.zip"
    destination = tmp_path / source_zip.name
    shutil.copy(source_zip, destination)
    return destination


def test_field_names():
    assert ALTOInput.field_names == (*FileInput.field_names, "section_type")


def test_get_text_iterates_xml(alto_sample_zip, caplog):
    alto_input = ALTOInput(input_file=alto_sample_zip)

    with caplog.at_level(logging.INFO, logger="remarx.sentence.corpus.alto_input"):
        chunks = list(alto_input.get_text())

    expected_files = [
        "1896-97a.pdf_page_1.xml",
        "1896-97a.pdf_page_2.xml",
        "1896-97a.pdf_page_3.xml",
        "1896-97a.pdf_page_4.xml",
        "1896-97a.pdf_page_5.xml",
        "empty_page.xml",
    ]

    assert alto_input._alto_members == sorted(expected_files)
    assert len(chunks) == len(expected_files)
    assert all(chunk["section_type"] == SectionType.TEXT.value for chunk in chunks)

    archive_to_chunk = dict(zip(alto_input._alto_members, chunks, strict=False))
    first_page_text = archive_to_chunk["1896-97a.pdf_page_1.xml"]["text"]
    assert "Die Neue Zeit." in first_page_text  # codespell:ignore
    assert "Arbeiter und Gewerbeausstellung." in first_page_text  # codespell:ignore
    assert "\n" in first_page_text

    processed_files = [
        record.getMessage().removeprefix("Processing ALTO XML file: ").strip()
        for record in caplog.records
        if record.name == "remarx.sentence.corpus.alto_input"
        and record.getMessage().startswith("Processing ALTO XML file: ")
    ]
    assert sorted(processed_files) == sorted(expected_files)


def test_validate_archive_success(alto_sample_zip):
    alto_input = ALTOInput(input_file=alto_sample_zip)
    # Should not raise
    alto_input.validate_archive()
    # Second call should reuse cached validation flag without error
    alto_input.validate_archive()
    assert alto_input._alto_members == sorted(
        [
            "1896-97a.pdf_page_1.xml",
            "1896-97a.pdf_page_2.xml",
            "1896-97a.pdf_page_3.xml",
            "1896-97a.pdf_page_4.xml",
            "1896-97a.pdf_page_5.xml",
            "empty_page.xml",
        ]
    )


def test_validate_archive_warns_on_no_text(alto_sample_zip, caplog):
    alto_input = ALTOInput(input_file=alto_sample_zip)
    with caplog.at_level(logging.WARNING, logger="remarx.sentence.corpus.alto_input"):
        alto_input.validate_archive()

    warning_messages = [
        record.getMessage()
        for record in caplog.records
        if record.name == "remarx.sentence.corpus.alto_input"
    ]
    assert any(
        message == "No text content found in ALTO XML file: empty_page.xml"
        for message in warning_messages
    )
    assert alto_input._chunk_cache["empty_page.xml"][0]["text"] == ""


def test_validate_archive_rejects_non_xml(tmp_path: Path):
    archive_path = tmp_path / "invalid.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("page1.txt", "not xml file")

    alto_input = ALTOInput(input_file=archive_path)
    with pytest.raises(ValueError, match="does not contain any valid ALTO XML files"):
        alto_input.validate_archive()


def test_validate_archive_rejects_non_alto_xml(tmp_path: Path):
    archive_path = tmp_path / "not_alto.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("page1.xml", "<root></root>")

    alto_input = ALTOInput(input_file=archive_path)
    with pytest.raises(ValueError, match="does not contain any valid ALTO XML files"):
        alto_input.validate_archive()


def test_validate_archive_rejects_unknown_namespace(tmp_path: Path):
    archive_path = tmp_path / "unknown_ns.zip"
    xml_content = '<alto xmlns="http://unknown_namespace.com/alto/ns#"><Description></Description></alto>'
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("page1.xml", xml_content)

    alto_input = ALTOInput(input_file=archive_path)
    with pytest.raises(ValueError, match="does not contain any valid ALTO XML files"):
        alto_input.validate_archive()


def test_validate_archive_logs_invalid_xml(tmp_path: Path, caplog):
    archive_path = tmp_path / "invalid_xml.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("page1.xml", "<alto>")

    alto_input = ALTOInput(input_file=archive_path)
    with (
        caplog.at_level(logging.WARNING, logger="remarx.sentence.corpus.alto_input"),
        pytest.raises(ValueError, match="does not contain any valid ALTO XML files"),
    ):
        alto_input.validate_archive()

    warning_messages = [
        record.getMessage()
        for record in caplog.records
        if record.name == "remarx.sentence.corpus.alto_input"
    ]
    assert any(
        message == "Skipping ALTO zipfile member with invalid XML: page1.xml"
        for message in warning_messages
    )


def test_text_line_str_returns_text(alto_sample_zip):
    with (
        ZipFile(alto_sample_zip) as archive,
        archive.open("1896-97a.pdf_page_1.xml") as xmlfile,
    ):
        doc = xmlmap.load_xmlobject_from_file(xmlfile, AltoDocument)

    first_line = doc.blocks[0].lines[0]
    assert str(first_line) == first_line.text_content


def test_validate_archive_rejects_empty_zip(tmp_path: Path):
    archive_path = tmp_path / "empty.zip"
    with ZipFile(archive_path, "w"):
        pass

    alto_input = ALTOInput(input_file=archive_path)
    with pytest.raises(ValueError, match="does not contain any valid ALTO XML files"):
        alto_input.validate_archive()
