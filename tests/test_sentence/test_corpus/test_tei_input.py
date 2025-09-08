import pathlib
from collections.abc import Generator
from unittest.mock import Mock, patch

import pytest

from remarx.sentence.corpus.tei_input import TEI_TAG, TEIDocument, TEIinput, TEIPage

FIXTURE_DIR = pathlib.Path(__file__).parent / "fixtures"
TEST_TEI_FILE = FIXTURE_DIR / "sample_tei.xml"


def test_tei_tag():
    # test that tei tags object is constructed as expected
    assert TEI_TAG.pb == "{http://www.tei-c.org/ns/1.0}pb"


class TestTEIDocument:
    def test_init_from_file(self):
        tei_doc = TEIDocument.init_from_file(TEST_TEI_FILE)
        assert isinstance(tei_doc, TEIDocument)
        # fixture currently includes 4 pb tags, 2 of which are manuscript edition
        assert len(tei_doc.all_pages) == 4
        assert isinstance(tei_doc.all_pages[0], TEIPage)
        # first pb in sample is n=12
        assert tei_doc.all_pages[0].number == "12"

    def test_init_error(self, tmp_path: pathlib.Path):
        txtfile = tmp_path / "non-tei.txt"
        txtfile.write_text("this is not tei or xml")
        with pytest.raises(ValueError, match="Error parsing"):
            TEIDocument.init_from_file(txtfile)

    def test_pages(self):
        tei_doc = TEIDocument.init_from_file(TEST_TEI_FILE)
        # pages should be filtered to the standard edition only
        assert len(tei_doc.pages) == 2
        # for these pages, edition attribute is not present
        assert all(p.edition is None for p in tei_doc.pages)


class TestTEIPage:
    def test_attributes(self):
        tei_doc = TEIDocument.init_from_file(TEST_TEI_FILE)
        # test first page and first manuscript page
        page = tei_doc.all_pages[0]
        ms_page = tei_doc.all_pages[1]

        assert page.number == "12"
        assert page.edition is None

        assert ms_page.number == "IX"
        assert ms_page.edition == "manuscript"

    def test_str(self):
        tei_doc = TEIDocument.init_from_file(TEST_TEI_FILE)
        # test first page
        page = tei_doc.all_pages[0]
        # includes some leading whitespace from <pb> and <p> tags
        # remove whitespace for testing for now
        text = str(page).strip()

        # first text content after the pb tag
        assert text.startswith("als in der ersten Darstellung.")  # codespell:ignore
        # last text content after the next standard pb tag
        assert text.endswith("entwickelten nur das Bild der eignen Zukunft!")
        # should not include editorial content
        assert "|" not in text
        assert "IX" not in text
        # TODO: eventually should not include footnote content


class TestTEIinput:
    def test_init(self):
        tei_input = TEIinput(input_file=TEST_TEI_FILE)
        assert tei_input.input_file == TEST_TEI_FILE
        # xml is parsed as tei document
        assert isinstance(tei_input.xml_doc, TEIDocument)

    def test_field_names(self, tmp_path: pathlib.Path):
        # includes defaults from text input and adds page number
        assert TEIinput.field_names == ("file", "sent_index", "text", "page_number")

    def test_get_text(self):
        tei_input = TEIinput(input_file=TEST_TEI_FILE)
        text_result = tei_input.get_text()
        # should be a generator
        assert isinstance(text_result, Generator)
        text_result = list(text_result)
        # expect two pages
        assert len(text_result) == 2
        # result type is dictionary
        assert all(isinstance(txt, dict) for txt in text_result)
        # check for expected contents
        # - page text
        assert (
            text_result[0]["text"]
            .strip()
            .startswith("als in der ersten")  # codespell:ignore
        )
        assert text_result[1]["text"].strip().startswith("Aber abgesehn hiervon")
        # - page number
        assert text_result[0]["page_number"] == "12"
        assert text_result[1]["page_number"] == "13"

    @patch("remarx.sentence.corpus.base_input.segment_text")
    def test_get_sentences(self, mock_segment_text: Mock):
        tei_input = TEIinput(input_file=TEST_TEI_FILE)
        # segment text returns a tuple of character index, sentence text
        mock_segment_text.return_value = [(0, "Aber abgesehn hiervon")]
        sentences = tei_input.get_sentences()
        # expect a generator with one item, with the content added to the file
        assert isinstance(sentences, Generator)
        sentences = list(sentences)
        assert len(sentences) == 2  # 2 pages, one mock sentence each
        # method called once for each page of text
        assert mock_segment_text.call_count == 2
        assert all(isinstance(sentence, dict) for sentence in sentences)
        # file id set (handled by base input class)
        assert sentences[0]["file"] == TEST_TEI_FILE.name
        # page number set
        assert sentences[0]["page_number"] == "12"
        assert sentences[1]["page_number"] == "13"
        # sentence index is set and continues across pages
        assert sentences[0]["sent_index"] == 0
        assert sentences[1]["sent_index"] == 1
