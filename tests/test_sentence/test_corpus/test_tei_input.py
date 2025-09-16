import pathlib
from collections.abc import Generator
from unittest.mock import Mock, patch

import pytest
from lxml.etree import Element

from remarx.sentence.corpus.base_input import FileInput
from remarx.sentence.corpus.tei_input import TEI_TAG, TEIDocument, TEIinput, TEIPage

FIXTURE_DIR = pathlib.Path(__file__).parent / "fixtures"
TEST_TEI_FILE = FIXTURE_DIR / "sample_tei.xml"
TEST_TEI_WITH_FOOTNOTES_FILE = FIXTURE_DIR / "sample_tei_with_footnotes.xml"


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

    @patch.object(TEIPage, "get_body_text")
    @patch.object(TEIPage, "get_footnote_text")
    def test_str(self, mock_get_footnote_text, mock_get_body_text):
        mock_get_body_text.return_value = "Mock body text"
        mock_get_footnote_text.return_value = "Mock footnote text"

        tei_doc = TEIDocument.init_from_file(TEST_TEI_FILE)
        page = tei_doc.all_pages[0]

        result = str(page)

        # Verify mocks were called (may be called multiple times)
        assert mock_get_body_text.called
        assert mock_get_footnote_text.called

        # should return both body text and footnote text, separated by double newlines
        assert result == "Mock body text\n\nMock footnote text"

    def test_get_body_text_no_footnotes(self):
        tei_doc = TEIDocument.init_from_file(TEST_TEI_FILE)
        # test first page
        page = tei_doc.all_pages[0]
        # includes some leading whitespace from <pb> and <p> tags
        # remove whitespace for testing for now
        text = page.get_body_text()

        # Should not contain leading or trailing whitespace
        assert text == text.strip()
        # first text content after the pb tag
        assert text.startswith("als in der ersten Darstellung.")  # codespell:ignore
        # last text content after the next standard pb tag
        assert text.endswith("entwickelten nur das Bild der eignen Zukunft!")
        # should not include editorial content
        assert "|" not in text
        assert "IX" not in text

    def test_get_body_text_with_footnotes(self):
        # test a sample page with footnotes to confirm footnote contents are excluded
        tei_doc = TEIDocument.init_from_file(TEST_TEI_WITH_FOOTNOTES_FILE)
        page_17 = next(p for p in tei_doc.all_pages if p.number == "17")

        body_text = page_17.get_body_text()
        assert body_text.startswith(
            "Der Reichthum der Gesellschaften"
        )  # codespell:ignore
        assert "1) Karl Marx:" not in body_text  # Footnote content should be excluded

    def test_get_footnote_text_with_footnotes(self):
        tei_doc = TEIDocument.init_from_file(TEST_TEI_WITH_FOOTNOTES_FILE)
        page_17 = next(p for p in tei_doc.all_pages if p.number == "17")

        footnote_text = page_17.get_footnote_text()
        assert footnote_text.startswith("1) Karl Marx:")
        assert "Nicholas Barbon" in footnote_text
        assert (
            "Der Reichthum der Gesellschaften" not in footnote_text
        )  # Body text should be excluded

    def test_get_footnote_text_delimiter(self):
        # Test that footnotes are properly separated by double newlines
        tei_doc = TEIDocument.init_from_file(TEST_TEI_WITH_FOOTNOTES_FILE)
        page_17 = next(p for p in tei_doc.all_pages if p.number == "17")

        footnote_text = page_17.get_footnote_text()
        # Check that double newlines are present between footnotes
        # The fixture should have multiple footnotes to test this properly
        assert (
            "\n\n" in footnote_text
            or len(list(page_17.get_individual_footnotes())) <= 1
        )

    def test_is_footnote_content(self):
        # Test direct footnote elements
        footnote_ref = Element(TEI_TAG.ref, type="footnote")
        footnote_note = Element(TEI_TAG.note, type="footnote")
        regular_element = Element("p")

        assert TEIPage.is_footnote_content(footnote_ref)
        assert TEIPage.is_footnote_content(footnote_note)
        assert not TEIPage.is_footnote_content(regular_element)

        # Test nested elements within footnotes
        # Create sample XML tree to mimic the structure of a footnote:
        # <note type="footnote"><p><em>text</em></p></note>
        footnote_container = Element(
            TEI_TAG.note, type="footnote"
        )  # create a footnote container element
        paragraph = Element("p")  # create a paragraph element
        emphasis = Element("em")  # create an emphasis element

        footnote_container.append(
            paragraph
        )  # nest the paragraph element within the footnote container
        paragraph.append(
            emphasis
        )  # nest the emphasis element within the paragraph element

        # Test that nested elements are correctly identified as footnote content
        assert TEIPage.is_footnote_content(paragraph)
        assert TEIPage.is_footnote_content(emphasis)

        # Test element outside footnote structure
        standalone_p = Element("p")
        assert not TEIPage.is_footnote_content(standalone_p)


class TestTEIinput:
    def test_init(self):
        tei_input = TEIinput(input_file=TEST_TEI_FILE)
        assert tei_input.input_file == TEST_TEI_FILE
        # xml is parsed as tei document
        assert isinstance(tei_input.xml_doc, TEIDocument)

    def test_field_names(self):
        # includes defaults from text input and adds page number and section type
        assert TEIinput.field_names == (
            *FileInput.field_names,
            "page_number",
            "section_type",
        )

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
        # - section type
        assert text_result[0]["section_type"] == "text"
        assert text_result[1]["section_type"] == "text"

    def test_get_text_with_footnotes(self):
        tei_input = TEIinput(input_file=TEST_TEI_WITH_FOOTNOTES_FILE)
        text_chunks = list(tei_input.get_text())

        # Should get both text and footnote chunks for each page
        section_types = [chunk["section_type"] for chunk in text_chunks]
        assert "text" in section_types
        assert "footnote" in section_types

        # Check page numbers are set correctly
        assert all("page_number" in chunk for chunk in text_chunks)
        assert all(isinstance(chunk["text"], str) for chunk in text_chunks)

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

    @patch("remarx.sentence.corpus.base_input.segment_text")
    def test_get_sentences_with_footnotes(self, mock_segment_text: Mock):
        tei_input = TEIinput(input_file=TEST_TEI_WITH_FOOTNOTES_FILE)
        # segment text returns a tuple of character index, sentence text
        mock_segment_text.return_value = [(0, "Aber abgesehn hiervon")]
        sentences = tei_input.get_sentences()
        # expect a generator
        assert isinstance(sentences, Generator)
        sentences = list(sentences)
        # all should be dictionaries
        assert all(isinstance(sentence, dict) for sentence in sentences)
        # should have both text and footnote sections
        section_types = [s["section_type"] for s in sentences]
        assert "text" in section_types
        assert "footnote" in section_types
