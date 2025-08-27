import pathlib
from unittest.mock import Mock, patch

import pytest
from lxml.etree import Element

from remarx.sentence.corpus.tei_input import TEI_TAG, TEIDocument, TEIinput, TEIPage

FIXTURE_DIR = pathlib.Path(__file__).parent / "fixtures"
TEST_TEI_FILE = FIXTURE_DIR / "sample_tei.xml"
TEST_TEI_WITH_FOOTNOTES_FILE = FIXTURE_DIR / "sample_tei_with_footnotes.xml"


def test_tei_tag():
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

    @patch.object(TEIPage, "get_body_text")
    @patch.object(TEIPage, "get_footnote_text")
    def test_str(self, mock_get_footnote_text, mock_get_body_text):
        mock_get_body_text.return_value = "Mock body text"
        mock_get_footnote_text.return_value = "Mock footnote text"

        tei_doc = TEIDocument.init_from_file(TEST_TEI_FILE)
        page = tei_doc.all_pages[0]

        result = str(page)

        mock_get_body_text.assert_called_once()
        mock_get_footnote_text.assert_called_once()

        # should return both body text and footnote text, separated by double newlines
        assert result == "Mock body text\n\nMock footnote text"

    def test_get_body_text_no_footnotes(self):
        tei_doc = TEIDocument.init_from_file(TEST_TEI_FILE)
        page = tei_doc.all_pages[0]

        body_text = page.get_body_text()
        assert "als in der ersten" in body_text  # codespell:ignore
        assert "Karl Marx:" not in body_text  # Should not contain footnote content

    def test_get_body_text_with_footnotes(self):
        tei_doc = TEIDocument.init_from_file(TEST_TEI_WITH_FOOTNOTES_FILE)
        page_17 = next(p for p in tei_doc.all_pages if p.number == "17")

        body_text = page_17.get_body_text()
        assert "Der Reichthum der Gesellschaften" in body_text  # codespell:ignore
        assert "Karl Marx:" not in body_text  # Footnote content should be excluded

    def test_get_footnote_text_no_footnotes(self):
        tei_doc = TEIDocument.init_from_file(TEST_TEI_FILE)
        page = tei_doc.all_pages[0]

        footnote_text = page.get_footnote_text()
        assert footnote_text == ""

    def test_get_footnote_text_with_footnotes(self):
        tei_doc = TEIDocument.init_from_file(TEST_TEI_WITH_FOOTNOTES_FILE)
        page_17 = next(p for p in tei_doc.all_pages if p.number == "17")

        footnote_text = page_17.get_footnote_text()
        assert "Karl Marx:" in footnote_text
        assert "Nicholas Barbon" in footnote_text
        assert (
            "Der Reichthum der Gesellschaften" not in footnote_text
        )  # Body text should be excluded

    def test_is_footnote_content(self):
        footnote_ref = Element(TEI_TAG.ref, type="footnote")
        footnote_note = Element(TEI_TAG.note, type="footnote")
        regular_element = Element("p")

        assert TEIPage.is_footnote_content(footnote_ref) is True
        assert TEIPage.is_footnote_content(footnote_note) is True
        assert TEIPage.is_footnote_content(regular_element) is False
        assert TEIPage.is_footnote_content(footnote_ref)
        assert TEIPage.is_footnote_content(footnote_note)
        assert not TEIPage.is_footnote_content(regular_element)


class TestTEIinput:
    def test_init(self):
        tei_input = TEIinput(input_file=TEST_TEI_FILE)
        assert isinstance(tei_input.xml_doc, TEIDocument)
        assert len(tei_input.xml_doc.pages) == 2

    def test_field_names(self):
        expected_fields = ("file", "offset", "text", "page_number", "section_type")
        assert TEIinput.field_names == expected_fields

    def test_get_text(self):
        tei_input = TEIinput(input_file=TEST_TEI_FILE)
        text_result = list(tei_input.get_text())

        assert len(text_result) == 2
        assert all(isinstance(txt, dict) for txt in text_result)
        assert "in der ersten Darstellung" in text_result[0]["text"]  # codespell:ignore
        assert text_result[0]["page_number"] == "12"
        assert text_result[0]["section_type"] == "text"

    def test_get_text_with_footnotes(self):
        tei_input = TEIinput(input_file=TEST_TEI_WITH_FOOTNOTES_FILE)
        text_chunks = list(tei_input.get_text())

        section_types = [chunk["section_type"] for chunk in text_chunks]
        assert "text" in section_types
        assert "footnote" in section_types

    @patch.object(TEIinput, "get_text")
    @patch("remarx.sentence.corpus.base_input.segment_text")
    def test_get_sentences(self, mock_segment_text: Mock, mock_get_text: Mock):
        # Mock get_text to return controlled text chunks
        mock_get_text.return_value = [
            {"text": "Sample body text.", "page_number": "12", "section_type": "text"},
            {
                "text": "Sample footnote text.",
                "page_number": "12",
                "section_type": "footnote",
            },
        ]
        mock_segment_text.side_effect = lambda text: [(0, text[:10]), (10, text[10:])]

        tei_input = TEIinput(input_file=TEST_TEI_FILE)
        sentences = list(tei_input.get_sentences())
        # Verify all calls had string arguments
        for call_args in mock_segment_text.call_args_list:
            assert len(call_args[0]) == 1  # One positional argument
            assert isinstance(call_args[0][0], str)  # Should be a string

        # Verify sentence structure
        assert len(sentences) > 0
        assert all(isinstance(sentence, dict) for sentence in sentences)
        assert sentences[0]["file"] == TEST_TEI_FILE.name

        # Check consecutive indexing
        sent_indices = [s["sent_index"] for s in sentences]
        assert sent_indices == list(range(len(sentences)))

    @patch.object(TEIinput, "get_text")
    @patch("remarx.sentence.corpus.base_input.segment_text")
    def test_get_sentences_with_footnotes(
        self, mock_segment_text: Mock, mock_get_text: Mock
    ):
        # Mock get_text to return both text and footnote chunks
        mock_get_text.return_value = [
            {"text": "Body text content.", "page_number": "17", "section_type": "text"},
            {
                "text": "Footnote content.",
                "page_number": "17",
                "section_type": "footnote",
            },
        ]
        mock_segment_text.side_effect = lambda text: [(0, text[:8]), (8, text[8:])]

        tei_input = TEIinput(input_file=TEST_TEI_WITH_FOOTNOTES_FILE)
        sentences = list(tei_input.get_sentences())

        # Verify all calls had string arguments
        for call_args in mock_segment_text.call_args_list:
            assert len(call_args[0]) == 1  # One positional argument
            assert isinstance(call_args[0][0], str)  # Should be a string

        # Check consecutive indexing
        sent_indices = [s["sent_index"] for s in sentences]
        assert sent_indices == list(range(len(sentences)))

        # Should have both text and footnote sections
        section_types = [s["section_type"] for s in sentences]
        assert "text" in section_types
        assert "footnote" in section_types
