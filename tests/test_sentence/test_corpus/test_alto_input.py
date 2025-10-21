import logging
import pathlib
from zipfile import ZipFile

import pytest
from neuxml import xmlmap

from remarx.sentence.corpus.alto_input import (
    AltoDocument,
    ALTOInput,
    TextBlock,
    TextLine,
)
from remarx.sentence.corpus.base_input import FileInput, SectionType

FIXTURE_DIR = pathlib.Path(__file__).parent / "fixtures"
FIXTURE_ALTO_ZIPFILE = FIXTURE_DIR / "alto_sample.zip"
FIXTURE_ALTO_PAGE = FIXTURE_DIR / "alto_page.xml"

# text xmlmap classes


def test_alto_document():
    altoxml = xmlmap.load_xmlobject_from_file(FIXTURE_ALTO_PAGE, AltoDocument)
    # sample page has 4 text blocks
    assert len(altoxml.blocks) == 4
    assert isinstance(altoxml.blocks[0], TextBlock)


def test_alto_document_is_alto():
    # sample page is alto
    altoxml = xmlmap.load_xmlobject_from_file(FIXTURE_ALTO_PAGE, AltoDocument)
    assert altoxml.is_alto()

    # load tei fixture as alto document to check non-alto content
    teixml = xmlmap.load_xmlobject_from_file(
        FIXTURE_DIR / "sample_tei.xml", AltoDocument
    )
    assert not teixml.is_alto()


def test_alto_textblock():
    altoxml = xmlmap.load_xmlobject_from_file(FIXTURE_ALTO_PAGE, AltoDocument)
    alto_textblock = altoxml.blocks[0]
    assert alto_textblock.horizontal_position == 728.0
    assert alto_textblock.vertical_position == 200.0
    assert len(alto_textblock.lines) == 1
    assert isinstance(alto_textblock.lines[0], TextLine)


def test_alto_textline():
    altoxml = xmlmap.load_xmlobject_from_file(FIXTURE_ALTO_PAGE, AltoDocument)
    alto_textline = altoxml.blocks[0].lines[0]
    assert alto_textline.horizontal_position == 868.0
    assert alto_textline.vertical_position == 256.0
    assert (
        alto_textline.text_content
        == "F. A. Sorge: Die Präsidentenwahl in den Vereinigten Staaten."
    )
    assert str(alto_textline) == alto_textline.text_content


# test file input classes


def test_field_names():
    assert ALTOInput.field_names == (*FileInput.field_names, "section_type")


def test_get_text_iterates_xml(caplog):
    alto_input = ALTOInput(input_file=FIXTURE_ALTO_ZIPFILE)

    with caplog.at_level(logging.INFO, logger="remarx.sentence.corpus.alto_input"):
        chunks = list(alto_input.get_text())

    expected_files = [
        "1896-97a.pdf_page_1.xml",
        "1896-97a.pdf_page_2.xml",
        "1896-97a.pdf_page_3.xml",
        "1896-97a.pdf_page_4.xml",
        "1896-97a.pdf_page_5.xml",
        "empty_page.xml",
        "unsorted_page.xml",
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


def test_validate_archive_success():
    alto_input = ALTOInput(input_file=FIXTURE_ALTO_ZIPFILE)
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
            "unsorted_page.xml",
        ]
    )


def test_validate_archive_warns_on_no_text(caplog):
    alto_input = ALTOInput(input_file=FIXTURE_ALTO_ZIPFILE)
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


def test_validate_archive_rejects_non_xml(tmp_path: pathlib.Path):
    archive_path = tmp_path / "invalid.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("page1.txt", "not xml file")

    alto_input = ALTOInput(input_file=archive_path)
    with pytest.raises(ValueError, match="does not contain any valid ALTO XML files"):
        alto_input.validate_archive()


def test_validate_archive_rejects_non_alto_xml(tmp_path: pathlib.Path):
    archive_path = tmp_path / "not_alto.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("page1.xml", "<root></root>")

    alto_input = ALTOInput(input_file=archive_path)
    with pytest.raises(ValueError, match="does not contain any valid ALTO XML files"):
        alto_input.validate_archive()


def test_validate_archive_rejects_unknown_namespace(tmp_path: pathlib.Path):
    archive_path = tmp_path / "unknown_ns.zip"
    xml_content = '<alto xmlns="http://unknown_namespace.com/alto/ns#"><Description></Description></alto>'
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("page1.xml", xml_content)

    alto_input = ALTOInput(input_file=archive_path)
    with pytest.raises(ValueError, match="does not contain any valid ALTO XML files"):
        alto_input.validate_archive()


def test_validate_archive_logs_invalid_xml(tmp_path: pathlib.Path, caplog):
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
        message == "Skipping ALTO file page1.xml : invalid XML"
        for message in warning_messages
    )


def test_text_line_str_returns_text():
    with (
        ZipFile(FIXTURE_ALTO_ZIPFILE) as archive,
        archive.open("1896-97a.pdf_page_1.xml") as xmlfile,
    ):
        doc = xmlmap.load_xmlobject_from_file(xmlfile, AltoDocument)

    first_line = doc.blocks[0].lines[0]
    assert str(first_line) == first_line.text_content


def test_get_text_sorts_by_vpos():
    # Test chunk text for a single ALTO page is ordered by HPOS
    alto_input = ALTOInput(input_file=FIXTURE_ALTO_ZIPFILE)
    chunks = list(alto_input.get_text())

    archive_to_chunk = dict(zip(alto_input._alto_members, chunks, strict=False))
    unsorted_text = archive_to_chunk["unsorted_page.xml"]["text"]

    assert unsorted_text.splitlines() == ["First line", "Second line"]


def test_get_sentences_indexes_sequential(monkeypatch):
    # Test cross-file sentence numbering also remains sequential once chunks
    # are converted into sentences.
    def simple_segmenter(text: str, language: str = "de"):
        sentences = []
        start_idx = 0
        for part in text.splitlines():
            part = part.strip()
            if not part:
                continue
            sentences.append((start_idx, part))
            start_idx += len(part) + 1
        if not sentences and text.strip():
            sentences.append((0, text.strip()))
        return sentences

    monkeypatch.setattr(
        "remarx.sentence.corpus.base_input.segment_text",
        simple_segmenter,
        raising=True,
    )

    alto_input = ALTOInput(input_file=FIXTURE_ALTO_ZIPFILE)
    sentences = list(alto_input.get_sentences())

    sent_indexes = [sentence["sent_index"] for sentence in sentences]
    assert sent_indexes == list(range(len(sent_indexes)))
    assert sentences[0]["sent_id"].endswith(":0")
    assert sentences[-1]["sent_index"] == len(sent_indexes) - 1


def test_validate_archive_rejects_empty_zip(tmp_path: pathlib.Path):
    archive_path = tmp_path / "empty.zip"
    with ZipFile(archive_path, "w"):
        pass

    alto_input = ALTOInput(input_file=archive_path)
    with pytest.raises(ValueError, match="does not contain any valid ALTO XML files"):
        alto_input.validate_archive()
