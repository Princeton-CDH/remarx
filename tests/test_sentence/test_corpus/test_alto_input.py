import logging
import pathlib
from collections import defaultdict
from collections.abc import Generator
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

# test xmlmap classes


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


def test_alto_document_sorted_blocks():
    altoxml = xmlmap.load_xmlobject_from_file(FIXTURE_ALTO_PAGE, AltoDocument)
    # sample alto page has been rearranged so text blocks are not sequential
    # by vertical position
    assert altoxml.blocks != altoxml.sorted_blocks
    # first block was moved to second, so 1 unsorted should match 0 sorted
    assert altoxml.blocks[1] == altoxml.sorted_blocks[0]
    # first block should be the smallest vpos on the page
    min_vpos = min(tb.vertical_position for tb in altoxml.blocks)
    assert altoxml.sorted_blocks[0].vertical_position == min_vpos


def test_alto_document_text_chunks():
    altoxml = xmlmap.load_xmlobject_from_file(FIXTURE_ALTO_PAGE, AltoDocument)
    chunks = altoxml.text_chunks()
    assert isinstance(chunks, Generator)
    # convert to list to verify contents
    chunks = list(chunks)
    # should be list of dict
    assert isinstance(chunks[0], dict)
    # should be one dict per text block
    assert len(chunks) == len(altoxml.blocks)
    assert chunks[0]["text"] == altoxml.sorted_blocks[0].text_content
    # for now, everything is text
    assert chunks[0]["section_type"] == SectionType.TEXT.value


def test_alto_textblock():
    altoxml = xmlmap.load_xmlobject_from_file(FIXTURE_ALTO_PAGE, AltoDocument)
    alto_textblock = altoxml.blocks[1]
    assert alto_textblock.horizontal_position == 728.0
    assert alto_textblock.vertical_position == 200.0
    assert len(alto_textblock.lines) == 1
    assert isinstance(alto_textblock.lines[0], TextLine)


def test_alto_textblock_sorted_lines():
    altoxml = xmlmap.load_xmlobject_from_file(FIXTURE_ALTO_PAGE, AltoDocument)
    # the third text block has the most lines;
    # lines 1 & 2 manually moved to force out of order
    alto_textblock = altoxml.blocks[2]
    assert alto_textblock.lines != alto_textblock.sorted_lines
    # first line  was moved to second, so 1 unsorted should match 0 sorted
    assert alto_textblock.lines[1] == alto_textblock.sorted_lines[0]
    # first line should be the smallest vpos on the page
    min_vpos = min(line.vertical_position for line in alto_textblock.lines)
    assert alto_textblock.sorted_lines[0].vertical_position == min_vpos


def test_alto_textblock_text_content():
    altoxml = xmlmap.load_xmlobject_from_file(FIXTURE_ALTO_PAGE, AltoDocument)

    alto_textblock = altoxml.blocks[3]
    block_text = alto_textblock.text_content
    # check that we have the expected number of lines
    assert len(block_text.split("\n")) == len(alto_textblock.lines)
    # and content starts and ends with expected contents
    assert block_text.startswith("Ist gegen die Klausel")  # codespell:ignore
    assert block_text.endswith("1896-97. I. Bd.")


def test_alto_textline():
    altoxml = xmlmap.load_xmlobject_from_file(FIXTURE_ALTO_PAGE, AltoDocument)
    alto_textline = altoxml.blocks[1].lines[0]
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


def test_altoinput_get_text(caplog):
    caplog.set_level(logging.INFO, logger="remarx.sentence.corpus.alto_input")
    alto_input = ALTOInput(input_file=FIXTURE_ALTO_ZIPFILE)
    chunks = alto_input.get_text()

    # confirm generator type, then convert to list to inspect results
    assert isinstance(chunks, Generator)
    chunks = list(chunks)
    assert isinstance(chunks[0], dict)

    expected_files = [
        "1896-97a.pdf_page_1.xml",
        "1896-97a.pdf_page_2.xml",
        "1896-97a.pdf_page_3.xml",
        "1896-97a.pdf_page_4.xml",
        "1896-97a.pdf_page_5.xml",
        "empty_page.xml",
        "unsorted_page.xml",
    ]

    # distinct filenames should match expected file list
    chunks_by_filename = defaultdict(list)
    for chunk in chunks:
        chunks_by_filename[chunk["file"]].append(chunk)

    assert set(chunks_by_filename.keys()) == set(expected_files)
    # all sections are currently text
    assert {chunk["section_type"] for chunk in chunks} == {SectionType.TEXT.value}

    # inspect text results for a few cases
    assert (
        chunks_by_filename["1896-97a.pdf_page_3.xml"][0]["text"]
        == "Arbeiter und Gewerbeausstellung."
    )
    assert chunks_by_filename["1896-97a.pdf_page_3.xml"][2]["text"].endswith(
        "langsamer und deshalb auch viel häßlicher und viel widerlicher. Und wie die"
    )

    processing_prefix = "Processing XML file "
    processed_files = [
        record.getMessage().removeprefix(processing_prefix)
        for record in caplog.records
        if record.getMessage().startswith(processing_prefix)
    ]
    assert sorted(processed_files) == sorted(expected_files)


@pytest.mark.skip
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


# is this a real problem?
@pytest.mark.skip
def test_altoinput_warn_no_text(caplog):
    alto_input = ALTOInput(input_file=FIXTURE_ALTO_ZIPFILE)
    with caplog.at_level(logging.WARNING, logger="remarx.sentence.corpus.alto_input"):
        list(alto_input.get_text())

    warning_messages = [record.getMessage() for record in caplog.records]
    assert any(
        message == "No text content found in ALTO XML file: empty_page.xml"
        for message in warning_messages
    )

    assert alto_input._chunk_cache["empty_page.xml"][0]["text"] == ""


def test_altoinput_error_non_xml(tmp_path: pathlib.Path):
    archive_path = tmp_path / "invalid.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("page1.txt", "not xml file")

    alto_input = ALTOInput(input_file=archive_path)
    with pytest.raises(
        ValueError, match=f"No valid ALTO XML files found in {archive_path}"
    ):
        list(alto_input.get_text())


def test_altoinput_error_non_alto_xml(tmp_path: pathlib.Path):
    archive_path = tmp_path / "not_alto.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("page1.xml", "<root></root>")

    alto_input = ALTOInput(input_file=archive_path)
    with pytest.raises(
        ValueError, match=f"No valid ALTO XML files found in {archive_path}"
    ):
        list(alto_input.get_text())


def test_altoinput_error_non_alto_xml_unknown_namespace(tmp_path: pathlib.Path):
    archive_path = tmp_path / "unknown_ns.zip"
    xml_content = '<alto xmlns="http://unknown_namespace.com/alto/ns#"><Description></Description></alto>'
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("page1.xml", xml_content)

    alto_input = ALTOInput(input_file=archive_path)
    with pytest.raises(
        ValueError, match=f"No valid ALTO XML files found in {archive_path}"
    ):
        list(alto_input.get_text())


def test_altoinput_warn_invalid_xml(tmp_path: pathlib.Path, caplog):
    archive_path = tmp_path / "invalid_xml.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("page1.xml", "<alto>")

    alto_input = ALTOInput(input_file=archive_path)
    caplog.set_level(logging.DEBUG, logger="remarx.sentence.corpus.alto_input")
    with pytest.raises(
        ValueError, match=f"No valid ALTO XML files found in {archive_path}"
    ):
        list(alto_input.get_text())

    # expect one warning message (skipping the file) and one debug (xml syntax error)
    warning_message = next(
        rec.getMessage() for rec in caplog.records if rec.levelname == "WARNING"
    )
    debug_message = next(
        rec.getMessage() for rec in caplog.records if rec.levelname == "DEBUG"
    )
    assert warning_message == "Skipping page1.xml : invalid XML"
    # debug message includes info about the syntax error
    assert "XML syntax error" in debug_message
    assert "Premature end of data in tag alto line 1" in debug_message


def test_altoinput_error_empty_zip(tmp_path: pathlib.Path):
    archive_path = tmp_path / "empty.zip"
    # create an empty but valid zipfile
    with ZipFile(archive_path, "w"):
        pass

    alto_input = ALTOInput(input_file=archive_path)
    with pytest.raises(
        ValueError, match=f"No valid ALTO XML files found in {archive_path}"
    ):
        list(alto_input.get_text())


@pytest.mark.skip
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
