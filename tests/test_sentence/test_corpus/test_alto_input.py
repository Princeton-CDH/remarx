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
    AltoTag,
    TextBlock,
    TextLine,
)
from remarx.sentence.corpus.base_input import FileInput
from test_sentence.test_corpus.test_text_input import simple_segmenter

FIXTURE_DIR = pathlib.Path(__file__).parent / "fixtures"
FIXTURE_ALTO_ZIPFILE = FIXTURE_DIR / "alto_sample.zip"
FIXTURE_ALTO_PAGE = FIXTURE_DIR / "alto_page.xml"
FIXTURE_ALTO_PAGE_WITH_FOOTNOTES = FIXTURE_DIR / "alto_page_with_footnote.xml"

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


def test_alto_document_tags():
    altoxml = xmlmap.load_xmlobject_from_file(FIXTURE_ALTO_PAGE, AltoDocument)
    # xmlobject list mapped to _tags
    assert isinstance(altoxml._tags[0], AltoTag)
    # dict property at named tags
    assert isinstance(altoxml.tags, dict)

    # fixture page has 13 tags
    assert len(altoxml.tags) == 13
    assert list(altoxml.tags.values()) == [
        "Title",
        "Main",
        "Commentary",
        "Illustration",
        "text",
        "Issue details",
        "Header",
        "page number",
        "section title",
        "Table",
        "footnote",
        "author",
        "default",
    ]
    # lookup tag label by id
    assert altoxml.tags["BT1"] == "Title"
    assert altoxml.tags["BT255"] == "footnote"


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
        "empty_page.xml",
        "unsorted_page.xml",
    ]

    # distinct filenames should match expected file list
    chunks_by_filename = defaultdict(list)
    for chunk in chunks:
        chunks_by_filename[chunk["file"]].append(chunk)

    assert set(chunks_by_filename.keys()) == set(expected_files)

    # check block tag section types for one file
    assert [
        chunk["section_type"] for chunk in chunks_by_filename["1896-97a.pdf_page_1.xml"]
    ] == ["Issue details", "Title", "text"]

    # inspect text results for a few cases
    assert (
        chunks_by_filename["1896-97a.pdf_page_3.xml"][0]["text"]
        == "Arbeiter und Gewerbeausstellung."
    )
    assert chunks_by_filename["1896-97a.pdf_page_3.xml"][2]["text"].endswith(
        "langsamer und deshalb auch viel häßlicher und viel widerlicher. Und wie die"
    )

    first_article = next(
        chunk
        for chunk in chunks_by_filename["1896-97a.pdf_page_1.xml"]
        if chunk["section_type"] == "text"
    )
    assert first_article["title"] == "Arbeiter und Gewerbeausstellung."
    assert first_article["author"] == ""

    continued_article = next(
        chunk
        for chunk in chunks_by_filename["1896-97a.pdf_page_2.xml"]
        if chunk["section_type"] == "text"
    )
    assert continued_article["title"] == first_article["title"]
    assert continued_article["author"] == ""

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
        f"Processed {FIXTURE_ALTO_ZIPFILE.name} with 7 files (7 valid ALTO)"
    )


def test_altoinput_get_text_filtered(caplog):
    # test filtering to only include text and footnotes
    alto_input = ALTOInput(input_file=FIXTURE_ALTO_ZIPFILE)
    filtered_chunks = alto_input.get_text()
    # this sample does not include any footnote blocks; only text + Title
    assert {chunk["section_type"] for chunk in filtered_chunks} == {"text", "Title"}


def test_altoinput_includes_title_and_author_metadata():
    alto_input = ALTOInput(input_file=FIXTURE_ALTO_ZIPFILE)
    chunks = list(alto_input.get_text())

    first_text = next(
        chunk
        for chunk in chunks
        if chunk["file"] == "1896-97a.pdf_page_1.xml"
        and chunk["section_type"] == "text"
    )
    assert first_text["title"] == "Arbeiter und Gewerbeausstellung."
    assert first_text["author"] == ""

    marx_text = next(
        chunk
        for chunk in chunks
        if chunk["file"] == "1896-97a.pdf_page_5.xml"
        and chunk["section_type"] == "text"
    )
    assert (
        marx_text["title"] == "Ein Brief von Karl Marx an I. B. v. Schweitzer über\n"
        "Lassalleanismus und Gewerkschaftskampf."
    )
    assert marx_text["author"] == "Vorbemerkung."


def test_altoinput_combines_sequential_title_author(tmp_path: pathlib.Path):
    archive_path = tmp_path / "single_page.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.write(FIXTURE_ALTO_PAGE, arcname="alto_page.xml")

    alto_input = ALTOInput(input_file=archive_path, filter_sections=False)
    chunks = list(alto_input.get_text())

    title_chunks = [
        chunk
        for chunk in chunks
        if chunk["section_type"] == "Title"
        and chunk["title"].startswith("Ein Brief von Karl Marx")
    ]
    assert (
        title_chunks[0]["title"]
        == "Ein Brief von Karl Marx an I. B. v. Schweitzer über"
    )
    assert (
        title_chunks[1]["title"]
        == "Ein Brief von Karl Marx an I. B. v. Schweitzer über\n"
        "Lassalleanismus und Gewerkschaftskampf."
    )

    article_chunk = next(
        chunk
        for chunk in chunks
        if chunk["section_type"] == "text"
        and chunk["text"].startswith("Im Nachlass von Karl Marx")
    )
    assert (
        article_chunk["title"]
        == "Ein Brief von Karl Marx an I. B. v. Schweitzer über\n"
        "Lassalleanismus und Gewerkschaftskampf."
    )
    assert article_chunk["author"] == "Vorbemerkung."

    intro_text_chunk = next(
        chunk
        for chunk in chunks
        if chunk["section_type"] == "text"
        and chunk["text"].startswith(
            "Die naturalistische Hochfluth ist vorüber"  # codespell:ignore
        )
    )
    assert intro_text_chunk["title"].startswith(
        "Der zweite, weit interessantere Band enthält nicht mehr gewöhnliche Salon"
    )

    split_title_chunk = next(
        chunk
        for chunk in chunks
        if chunk["section_type"] == "Title"
        and chunk["text"].startswith(
            "Die nächsten Aufgaben der deutschen Gewerkschafts-"
        )
    )
    assert (
        split_title_chunk["title"]
        == "Die nächsten Aufgaben der deutschen Gewerkschafts-\nbewegung."
    )

    split_article_chunk = next(
        chunk
        for chunk in chunks
        if chunk["section_type"] == "text"
        and chunk["text"].startswith("Ein altes Thema! So wird Mancher")
    )
    assert (
        split_article_chunk["title"]
        == "Die nächsten Aufgaben der deutschen Gewerkschafts-\nbewegung."
    )
    assert split_article_chunk["author"] == "Von G. Mauerer."


def test_altoinput_resets_metadata_on_blank_blocks(tmp_path: pathlib.Path):
    archive_path = tmp_path / "fixture_page.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.write(FIXTURE_ALTO_PAGE, arcname="alto_page.xml")

    alto_input = ALTOInput(input_file=archive_path, filter_sections=False)
    chunks = list(alto_input.get_text())

    section_title_chunk = next(
        chunk
        for chunk in chunks
        if chunk["section_type"] == "section title" and chunk["text"] == "Feuilleton."
    )
    assert section_title_chunk["title"] == ""
    assert section_title_chunk["author"] == ""

    new_article_chunk = next(
        chunk
        for chunk in chunks
        if chunk["section_type"] == "text"
        and chunk["text"].startswith("(Nachdruck verboten.)")
    )
    assert new_article_chunk["title"] == "Kämpfe."
    assert (
        new_article_chunk["author"]
        == "Von August Strindberg. Deutsch von Gustav Lichtenstein."
    )


def test_altoinput_preserves_title_through_blank_blocks(tmp_path: pathlib.Path):
    archive_path = tmp_path / "alto_fixture.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.write(FIXTURE_ALTO_PAGE, arcname="alto_page.xml")

    alto_input = ALTOInput(input_file=archive_path, filter_sections=False)
    chunks = list(alto_input.get_text())

    first_article_chunk = next(
        chunk
        for chunk in chunks
        if chunk["section_type"] == "text"
        and chunk["text"].startswith("Im Nachlass von Karl Marx")
    )
    assert (
        first_article_chunk["title"]
        == "Ein Brief von Karl Marx an I. B. v. Schweitzer über\n"
        "Lassalleanismus und Gewerkschaftskampf."
    )
    assert first_article_chunk["author"] == "Vorbemerkung."

    mid_article_chunk = next(
        chunk
        for chunk in chunks
        if chunk["section_type"] == "text"
        and chunk["text"].startswith("Die naturalistische Hochfluth")
    )
    assert mid_article_chunk["title"].startswith(
        "Der zweite, weit interessantere Band enthält"
    )

    section_chunk = next(
        chunk
        for chunk in chunks
        if chunk["section_type"] == "section title" and chunk["text"] == "Feuilleton."
    )
    assert section_chunk["title"] == ""
    assert section_chunk["author"] == ""

    new_article_body = next(
        chunk
        for chunk in chunks
        if chunk["section_type"] == "text"
        and chunk["text"].startswith("(Nachdruck verboten.)")
    )
    assert new_article_body["title"] == "Kämpfe."
    assert (
        new_article_body["author"]
        == "Von August Strindberg. Deutsch von Gustav Lichtenstein."
    )


def test_footnotes_inherit_article_metadata(tmp_path: pathlib.Path):
    archive_path = tmp_path / "alto_footnote_fixture.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.write(
            FIXTURE_ALTO_PAGE_WITH_FOOTNOTES, arcname="alto_page_with_footnote.xml"
        )

    alto_input = ALTOInput(input_file=archive_path)
    chunks = list(alto_input.get_text())

    # Find the footnote chunk
    footnote_chunk = next(
        chunk for chunk in chunks if chunk["section_type"] == "footnote"
    )
    assert footnote_chunk["title"] == "Ein Brief von Karl Marx an J. B. v. Schweitzer."
    assert footnote_chunk["author"] == "Der Herausgeber."
    assert "Historisch" in footnote_chunk["text"]
    assert "Manuskript" in footnote_chunk["text"]

    # Verify that text blocks also have the same metadata
    text_chunk = next(chunk for chunk in chunks if chunk["section_type"] == "text")
    assert text_chunk["title"] == "Ein Brief von Karl Marx an J. B. v. Schweitzer."
    assert text_chunk["author"] == "Der Herausgeber."


def test_update_article_metadata_sequences():
    alto_input = ALTOInput(input_file=FIXTURE_ALTO_ZIPFILE)
    # initialize fields as get_text would
    alto_input._current_title = ""
    alto_input._current_author = ""
    alto_input._collecting_title = False
    alto_input._collecting_author = False
    alto_input._pending_title_reset = False

    def apply(section: str, text: str) -> None:
        alto_input._update_article_metadata(section, text)

    apply("Title", "Article A")
    assert alto_input._current_title == "Article A"
    assert alto_input._current_author == ""

    apply("Title", "Subtitle")
    assert alto_input._current_title == "Article A\nSubtitle"

    apply("author", "Von Foo")
    assert alto_input._current_author == "Von Foo"

    apply("author", "Aus Bar")
    assert alto_input._current_author == "Von Foo\nAus Bar"

    apply("text", "Body text.")
    assert alto_input._current_title.startswith("Article A")

    # blank title should not immediately clear metadata
    apply("Title", "")
    assert alto_input._current_title.startswith("Article A")

    # next non-title block clears metadata
    apply("section title", "Feuilleton.")
    assert alto_input._current_title == ""
    assert alto_input._current_author == ""

    apply("Title", "Article B")
    assert alto_input._current_title == "Article B"
    assert alto_input._current_author == ""

    apply("author", "Von Example")
    assert alto_input._current_author == "Von Example"

    # blank title followed immediately by author should keep metadata
    apply("Title", "")
    apply("author", "Von Tail Author")
    assert alto_input._current_title == "Article B"
    assert alto_input._current_author == "Von Tail Author"

    # blank author clears current author metadata
    apply("author", "")
    assert alto_input._current_author == ""


def test_altoinput_warn_no_text(caplog):
    alto_input = ALTOInput(input_file=FIXTURE_ALTO_ZIPFILE)
    with caplog.at_level(logging.WARNING, logger="remarx.sentence.corpus.alto_input"):
        list(alto_input.get_text())

    warning_messages = [record.getMessage() for record in caplog.records]
    assert any(
        message == "No text lines found in ALTO XML file: empty_page.xml"
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
    # and filtering by section type expect 16 sentences
    assert num_sentences == 20

    # sentence indexes should start at 0 and continue across all sentences
    indexes = [sentence["sent_index"] for sentence in sentences]
    assert indexes == list(range(num_sentences))
