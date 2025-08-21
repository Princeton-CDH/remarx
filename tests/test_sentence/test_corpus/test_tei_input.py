import pathlib
from collections.abc import Generator
from unittest.mock import Mock, patch

import pytest

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

    def test_text_contents_no_footnotes(self):
        """Test text_contents for pages without footnotes."""
        tei_doc = TEIDocument.init_from_file(TEST_TEI_FILE)
        # test first page (no footnotes in sample, so should yield body text only)
        page = tei_doc.all_pages[0]

        sections = list(page.text_contents())
        # expect one section with body text
        assert len(sections) == 1

        text_content, section_type = sections[0]
        assert section_type == "text"
        assert text_content.strip().startswith("als in der ersten")  # codespell:ignore
        assert text_content.strip().endswith(
            "entwickelten nur das Bild der eignen Zukunft!"
        )

        # should not include editorial content
        assert "|" not in text_content
        assert "IX" not in text_content

    def test_text_contents_with_footnotes(self):
        """Test text_contents for pages with footnotes."""
        tei_doc = TEIDocument.init_from_file(TEST_TEI_WITH_FOOTNOTES_FILE)

        # Test page 17 which has footnotes
        page_17 = None
        for page in tei_doc.all_pages:
            if page.number == "17":
                page_17 = page
                break
        assert page_17 is not None, "Page 17 not found"

        sections = list(page_17.text_contents())

        # Should have 2 sections: body text + combined footnotes
        assert len(sections) == 2

        # First section should be body text
        body_text, body_type = sections[0]
        assert body_type == "text"
        assert "Der Reichthum der Gesellschaften" in body_text
        assert "Analyse der Waare" in body_text
        # Body text should NOT contain footnote content
        assert "Karl Marx:" not in body_text
        assert "Nicholas Barbon" not in body_text

        # Second section should be combined footnotes
        footnotes_text, footnotes_type = sections[1]
        assert footnotes_type == "footnote"
        # Should contain both footnotes
        assert "Karl Marx:" in footnotes_text
        assert "Zur Kritik der Politischen Oekonomie" in footnotes_text
        assert "Nicholas Barbon" in footnotes_text
        assert "Discourse on coining" in footnotes_text

    def test_text_contents_excludes_page_spanning_footnotes(self):
        """Test that footnotes spanning multiple pages are excluded."""
        tei_doc = TEIDocument.init_from_file(TEST_TEI_WITH_FOOTNOTES_FILE)

        # Test page 18 which has a footnote that spans to page 19
        page_18 = None
        for page in tei_doc.all_pages:
            if page.number == "18":
                page_18 = page
                break
        assert page_18 is not None, "Page 18 not found"

        sections = list(page_18.text_contents())

        # Should only have body text, no footnotes (footnote spans to page 19)
        assert len(sections) == 1

        body_text, body_type = sections[0]
        assert body_type == "text"
        assert "Die Nützlichkeit eines Dings" in body_text
        # Should not contain the page-spanning footnote content
        assert "Die natürliche Eigenschaft" not in body_text
        assert "John Locke" not in body_text


class TestTEIinput:
    def test_init(self):
        tei_input = TEIinput(input_file=TEST_TEI_FILE)
        assert tei_input.input_file == TEST_TEI_FILE
        # xml is parsed as tei document
        assert isinstance(tei_input.xml_doc, TEIDocument)

    def test_field_names(self, tmp_path: pathlib.Path):
        # includes defaults from text input and adds page number and section type
        assert TEIinput.field_names == (
            "file",
            "offset",
            "text",
            "sent_index",
            "page_number",
            "section_type",
        )

    def test_get_text(self):
        tei_input = TEIinput(input_file=TEST_TEI_FILE)
        text_result = tei_input.get_text()
        # should be a generator
        assert isinstance(text_result, Generator)
        text_result = list(text_result)
        # expect two pages, each with body text (no footnotes in this sample)
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
        # - section type (should be "text" for body content)
        assert text_result[0]["section_type"] == "text"
        assert text_result[1]["section_type"] == "text"

    @patch("remarx.sentence.corpus.text_input.segment_text")
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
        # section type is set to "text" for body content
        assert sentences[0]["section_type"] == "text"
        assert sentences[1]["section_type"] == "text"

    def test_get_text_with_footnotes(self):
        """Test get_text with file containing footnotes."""
        tei_input = TEIinput(input_file=TEST_TEI_WITH_FOOTNOTES_FILE)
        text_chunks = list(tei_input.get_text())

        # Should have multiple chunks including footnotes
        assert len(text_chunks) >= 3

        # Find page 17 chunks
        page_17_chunks = [
            chunk for chunk in text_chunks if chunk["page_number"] == "17"
        ]
        assert len(page_17_chunks) == 2  # body + combined footnotes

        # Check section types
        section_types = [chunk["section_type"] for chunk in page_17_chunks]
        assert "text" in section_types
        assert "footnote" in section_types
        assert section_types.count("footnote") == 1

        # Body text should come first
        assert page_17_chunks[0]["section_type"] == "text"
        assert "Der Reichthum der Gesellschaften" in page_17_chunks[0]["text"]

        # Combined footnotes should follow
        footnote_chunk = next(
            chunk for chunk in page_17_chunks if chunk["section_type"] == "footnote"
        )
        assert "Karl Marx:" in footnote_chunk["text"]
        assert "Nicholas Barbon" in footnote_chunk["text"]

    @patch("remarx.sentence.corpus.text_input.segment_text")
    def test_get_sentences_with_footnotes(self, mock_segment_text: Mock):
        """Test get_sentences maintains consecutive indexing across body and footnotes."""
        tei_input = TEIinput(input_file=TEST_TEI_WITH_FOOTNOTES_FILE)

        # Mock segment_text to return one sentence per chunk for predictable testing
        mock_segment_text.side_effect = lambda text: [(0, text.strip()[:50] + "...")]

        sentences = list(tei_input.get_sentences())

        # Should have sentences from multiple chunks (body + footnotes)
        assert len(sentences) >= 3

        # Check that sentence indexing is consecutive
        sent_indices = [sentence["sent_index"] for sentence in sentences]
        assert sent_indices == list(range(len(sentences)))

        # Should have both text and footnote sentences
        section_types = [sentence["section_type"] for sentence in sentences]
        assert "text" in section_types
        assert "footnote" in section_types

        # Find some footnote sentences
        footnote_sentences = [s for s in sentences if s["section_type"] == "footnote"]
        assert len(footnote_sentences) >= 1  # At least 1 footnote chunk on page 17
