import logging
import pathlib
from collections import defaultdict
from collections.abc import Generator
from unittest.mock import Mock, patch
from zipfile import ZipFile

import pytest
from natsort import natsorted
from neuxml import xmlmap

from remarx.sentence.corpus.alto_input import (
    AltoDocument,
    ALTOInput,
    TextBlock,
    TextLine,
)
from remarx.sentence.corpus.base_input import FileInput
from test_sentence.test_corpus.test_text_input import simple_segmenter

FIXTURE_DIR = pathlib.Path(__file__).parent / "fixtures"
FIXTURE_ALTO_ZIPFILE = FIXTURE_DIR / "alto_sample.zip"
FIXTURE_ALTO_PAGE = FIXTURE_DIR / "alto_page.xml"
FIXTURE_ALTO_PAGE_WITH_FOOTNOTES = FIXTURE_DIR / "alto_page_with_footnote.xml"
FIXTURE_ALTO_METADATA = FIXTURE_DIR / "alto_metadata.xml"

# test xmlmap classes


def test_alto_document():
    altoxml = xmlmap.load_xmlobject_from_file(FIXTURE_ALTO_PAGE, AltoDocument)
    # sample page has 19 text blocks
    assert len(altoxml.blocks) == 19
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

    # sorted logic when no text blocks
    empty_alto = xmlmap.load_xmlobject_from_string("<root/>", AltoDocument)
    assert empty_alto.sorted_blocks == []


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
    # section type is based on block tag labels in the alto
    assert [c["section_type"] for c in chunks] == [
        "Header",
        "page number",
        "text",
        "Title",
        "Title",
        "author",
        "text",
        "Title",
        "footnote",
        "text",
        "Title",
        "author",
        "text",
        "text",
        "Title",
        "section title",
        "Title",
        "author",
        "text",
    ]

    # optionally filter by type/block tag
    content_chunks = list(altoxml.text_chunks(include={"text", "footnote"}))
    assert len(content_chunks) == 7
    assert [chunk["section_type"] for chunk in content_chunks] == [
        "text",
        "text",
        "footnote",
        "text",
        "text",
        "text",
        "text",
    ]

    # ignores irrelevant tag
    other_chunks = list(altoxml.text_chunks(include={"Header", "foo"}))
    assert len(other_chunks) == 1
    assert other_chunks[0]["section_type"] == "Header"


def test_alto_textblock():
    altoxml = xmlmap.load_xmlobject_from_file(FIXTURE_ALTO_PAGE, AltoDocument)
    alto_textblock = altoxml.blocks[1]
    assert alto_textblock.horizontal_position == 728.0
    assert alto_textblock.vertical_position == 200.0
    assert len(alto_textblock.lines) == 1
    assert isinstance(alto_textblock.lines[0], TextLine)
    assert alto_textblock.tag_id == "BT251"
    assert alto_textblock.tag == "Header"

    # first block tag is page number
    assert altoxml.blocks[0].tag_id == "BT252"
    assert altoxml.blocks[0].tag == "page number"

    # handles no tag id
    # attribute is present but has no content
    alto_textblock.tag_id = None
    assert alto_textblock.tag is None
    # attribute is not present
    del alto_textblock.tag_id
    assert alto_textblock.tag is None


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

    alto_textblock = next(block for block in altoxml.blocks if block.tag_id == "BT255")
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
    assert ALTOInput.field_names == (
        *FileInput.field_names,
        "section_type",
        "title",
        "author",
        "page_number",
        "page_file",
    )


def test_altoinput_get_text(caplog):
    caplog.set_level(logging.INFO, logger="remarx.sentence.corpus.alto_input")
    # don't filter out by section label, for initial test
    alto_input = ALTOInput(input_file=FIXTURE_ALTO_ZIPFILE, filter_sections=False)
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
        "empty_page.xml",  # now skipped entirely
        "unsorted_page.xml",
    ]

    # distinct filenames should match expected file list
    chunks_by_filename = defaultdict(list)
    for chunk in chunks:
        chunks_by_filename[chunk["page_file"]].append(chunk)

    # empty page should not be present since no chunks are yielded
    assert set(chunks_by_filename.keys()) == set(expected_files) - {"empty_page.xml"}

    # check block tag section types for one file
    assert [
        chunk["section_type"] for chunk in chunks_by_filename["1896-97a.pdf_page_1.xml"]
    ] == ["Issue details", "Title", "text"]

    # title/author metadata tested separately below

    processing_prefix = "Processing XML file "
    processed_files = [
        record.getMessage().removeprefix(processing_prefix)
        for record in caplog.records
        if record.getMessage().startswith(processing_prefix)
    ]
    assert processed_files == natsorted(expected_files)

    # last log entry should report time to process, # of files
    summary_log_message = caplog.records[-1].getMessage()
    assert summary_log_message.startswith(
        # empty file now considered invalid
        f"Processed {FIXTURE_ALTO_ZIPFILE.name} with 7 files (6 valid ALTO)"
    )


def test_altoinput_get_text_filtered(caplog):
    # test filtering to only include text and footnotes
    alto_input = ALTOInput(input_file=FIXTURE_ALTO_ZIPFILE)
    filtered_chunks = alto_input.get_text()
    # this sample does not include any footnote blocks; only text + Title
    assert {chunk["section_type"] for chunk in filtered_chunks} == {"text", "Title"}


def test_altoinput_update_current_metadata():
    alto_input = ALTOInput(input_file=FIXTURE_ALTO_ZIPFILE)
    alto_input.current_metadata = {}
    alto_doc = xmlmap.load_xmlobject_from_file(FIXTURE_ALTO_METADATA, AltoDocument)

    # page text blocks start with Header, page number, then Title.
    # update metadata starting with title and all following blocks
    alto_input.update_current_metadata(alto_doc.sorted_blocks[2:])
    assert (
        alto_input.current_metadata["title"]
        == "Ein Brief von Karl Marx an I. B. v. Schweitzer über\n"
        + "Lassalleanismus und Gewerkschaftskampf."
    )
    assert alto_input.current_metadata["author"] == "Vorbemerkung."

    # if update is called  but no content is found, title/author are cleared
    alto_input.update_current_metadata(alto_doc.sorted_blocks[-1:])
    assert alto_input.current_metadata["title"] == ""
    assert alto_input.current_metadata["author"] == ""

    # test with other alto fixture document, which contains multiple title groups
    alto_doc = xmlmap.load_xmlobject_from_file(FIXTURE_ALTO_PAGE, AltoDocument)

    # first title / author section starts at block index 3
    alto_input.update_current_metadata(alto_doc.sorted_blocks[3:])
    assert (
        alto_input.current_metadata["title"]
        == "Ein Brief von Karl Marx an I. B. v. Schweitzer über "
        + "Lassalleanismus und Gewerkschaftskampf."
    )
    assert alto_input.current_metadata["author"] == "Vorbemerkung."

    # second title / author section starts at block index 7
    alto_input.update_current_metadata(alto_doc.sorted_blocks[7:])
    assert (
        alto_input.current_metadata["title"]
        == "Der zweite, weit interessantere Band enthält nicht mehr gewöhnliche Salon⸗"
        + "\nkritiken."
    )
    assert alto_input.current_metadata["author"] == ""

    # third title/author section starts at block index 10
    alto_input.update_current_metadata(alto_doc.sorted_blocks[10:])
    assert (
        alto_input.current_metadata["title"]
        == "Die nächsten Aufgaben der deutschen Gewerkschafts-\nbewegung."
    )
    assert alto_input.current_metadata["author"] == "Von G. Mauerer."

    # last title/author section starts at third from last block
    alto_input.update_current_metadata(alto_doc.sorted_blocks[-3:])
    assert alto_input.current_metadata["title"] == "Kämpfe."
    assert (
        alto_input.current_metadata["author"]
        == "Von August Strindberg. Deutsch von Gustav Lichtenstein."
    )


def test_altoinput_includes_title_and_author_metadata():
    alto_input = ALTOInput(input_file=FIXTURE_ALTO_ZIPFILE)
    chunks = list(alto_input.get_text())

    # get first text section from page 1 file
    first_text = next(
        chunk
        for chunk in chunks
        if chunk["page_file"] == "1896-97a.pdf_page_1.xml"
        and chunk["section_type"] == "text"
    )
    assert first_text["title"] == "Arbeiter und Gewerbeausstellung."
    assert first_text["author"] == ""
    # first page does not have a page number block
    assert "page_number" not in first_text

    # get the first text chunk from page 5 file
    marx_text = next(
        chunk
        for chunk in chunks
        if chunk["page_file"] == "1896-97a.pdf_page_5.xml"
        and chunk["section_type"] == "text"
    )
    assert (
        marx_text["title"] == "Ein Brief von Karl Marx an I. B. v. Schweitzer über\n"
        "Lassalleanismus und Gewerkschaftskampf."
    )
    assert marx_text["author"] == "Vorbemerkung."
    # page_5.xml has a text block marked as page number with text content 5
    assert marx_text["page_number"] == "5"


def test_footnotes_include_metadata(tmp_path: pathlib.Path):
    archive_path = tmp_path / "alto_footnote_fixture.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.write(
            FIXTURE_ALTO_PAGE_WITH_FOOTNOTES, arcname="alto_page_with_footnote.xml"
        )

    alto_input = ALTOInput(input_file=archive_path)
    chunks = list(alto_input.get_text())

    # Find the first footnote chunk
    footnote_chunk = next(
        chunk for chunk in chunks if chunk["section_type"] == "footnote"
    )
    assert footnote_chunk["title"] == "Ein Brief von Karl Marx an J. B. v. Schweitzer."
    assert footnote_chunk["author"] == "Der Herausgeber."
    assert footnote_chunk["page_number"] == "9"
    assert "Historisch" in footnote_chunk["text"]
    assert "Manuskript" in footnote_chunk["text"]

    # Verify that text blocks also have the same metadata
    text_chunk = next(chunk for chunk in chunks if chunk["section_type"] == "text")
    assert text_chunk["title"] == "Ein Brief von Karl Marx an J. B. v. Schweitzer."
    assert text_chunk["author"] == "Der Herausgeber."
    assert text_chunk["page_number"] == "9"


def test_altoinput_footnotes_emitted_last(tmp_path: pathlib.Path):
    archive_path = tmp_path / "alto_footnote_order.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.write(
            FIXTURE_ALTO_PAGE_WITH_FOOTNOTES,
            arcname="alto_page_with_footnote.xml",
        )

    alto_input = ALTOInput(input_file=archive_path)
    sections = [chunk["section_type"] for chunk in alto_input.get_text()]

    first_footnote_idx = sections.index("footnote")
    assert "footnote" not in sections[:first_footnote_idx]
    assert set(sections[first_footnote_idx:]) == {"footnote"}


def test_altoinput_warn_no_text(caplog):
    alto_input = ALTOInput(input_file=FIXTURE_ALTO_ZIPFILE)
    with caplog.at_level(logging.WARNING, logger="remarx.sentence.corpus.alto_input"):
        list(alto_input.get_text())

    warning_messages = [record.getMessage() for record in caplog.records]
    assert any(
        message == "No text lines in ALTO XML file: empty_page.xml"
        for message in warning_messages
    )


def test_altoinput_error_non_xml(tmp_path: pathlib.Path):
    archive_path = tmp_path / "invalid.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("page1.txt", "not xml file")

    alto_input = ALTOInput(input_file=archive_path)
    with pytest.raises(
        ValueError, match=f"No valid ALTO XML files found in {archive_path.name}"
    ):
        list(alto_input.get_text())


def test_altoinput_error_non_alto_xml(tmp_path: pathlib.Path):
    archive_path = tmp_path / "not_alto.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("page1.xml", "<root></root>")

    alto_input = ALTOInput(input_file=archive_path)
    with pytest.raises(
        ValueError, match=f"No valid ALTO XML files found in {archive_path.name}"
    ):
        list(alto_input.get_text())


def test_altoinput_error_non_alto_xml_unknown_namespace(tmp_path: pathlib.Path):
    archive_path = tmp_path / "unknown_ns.zip"
    xml_content = '<alto xmlns="http://unknown_namespace.com/alto/ns#"><Description></Description></alto>'
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("page1.xml", xml_content)

    alto_input = ALTOInput(input_file=archive_path)
    with pytest.raises(
        ValueError, match=f"No valid ALTO XML files found in {archive_path.name}"
    ):
        list(alto_input.get_text())


def test_altoinput_warn_invalid_xml(tmp_path: pathlib.Path, caplog):
    archive_path = tmp_path / "invalid_xml.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("page1.xml", "<alto>")

    alto_input = ALTOInput(input_file=archive_path)
    caplog.set_level(logging.DEBUG, logger="remarx.sentence.corpus.alto_input")
    with pytest.raises(
        ValueError, match=f"No valid ALTO XML files found in {archive_path.name}"
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
        ValueError, match=f"No valid ALTO XML files found in {archive_path.name}"
    ):
        list(alto_input.get_text())


@patch("remarx.sentence.corpus.base_input.segment_text")
def test_get_sentences_sequential(mock_segment_text: Mock):
    # patch in simple segmenter to split each input text in two
    mock_segment_text.side_effect = simple_segmenter

    alto_input = ALTOInput(input_file=FIXTURE_ALTO_ZIPFILE)
    sentences = list(alto_input.get_sentences())
    num_sentences = len(sentences)
    # currently with this fixture data and simple segmenter,
    # and filtering by section type expect 18 sentences
    assert num_sentences == 18

    # sentence indexes should start at 0 and continue across all sentences
    indexes = [sentence["sent_index"] for sentence in sentences]
    assert indexes == list(range(num_sentences))
