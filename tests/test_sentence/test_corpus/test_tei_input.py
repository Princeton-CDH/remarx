import pathlib
from collections.abc import Generator
from unittest.mock import Mock, patch

import pytest

from remarx.sentence.corpus.tei_input import TEI_TAG, TEIDocument, TEIinput, TEIPage

FIXTURE_DIR = pathlib.Path(__file__).parent / "fixtures"
TEST_TEI_FILE = FIXTURE_DIR / "sample_tei.xml"
TEST_TEI_WITH_FOOTNOTES_FILE = FIXTURE_DIR / "sample_tei_with_footnotes.xml"


@pytest.fixture
def tei_document_fixture():
    """Real TEIDocument fixture using actual XML."""
    return TEIDocument.init_from_file(TEST_TEI_FILE)


@pytest.fixture
def tei_document_with_footnotes_fixture():
    """Real TEIDocument fixture with footnotes using actual XML."""
    return TEIDocument.init_from_file(TEST_TEI_WITH_FOOTNOTES_FILE)


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
        """Test __str__ method for page with footnotes."""
        tei_doc = TEIDocument.init_from_file(TEST_TEI_WITH_FOOTNOTES_FILE)

        # Test page 17 which has footnotes
        page_17 = next(
            (page for page in tei_doc.all_pages if page.number == "17"), None
        )
        assert page_17 is not None, "Page 17 not found"

        page_text = str(page_17)

        # Should contain body text
        assert "Der Reichthum der Gesellschaften" in page_text
        assert "Analyse der Waare" in page_text

        # Should also contain footnote content (concatenated after body text)
        assert "Karl Marx:" in page_text
        assert "Zur Kritik der Politischen Oekonomie" in page_text
        assert "Nicholas Barbon" in page_text
        assert "Discourse on coining" in page_text

    def test_getters_no_footnotes(self):
        """Test body and footnote getters for pages without footnotes."""
        tei_doc = TEIDocument.init_from_file(TEST_TEI_FILE)
        # test first page (no footnotes in sample, so should yield body text only)
        page = tei_doc.all_pages[0]

        body_text = page.get_body_text()
        assert body_text.strip().startswith(
            "als in der ersten"  # codespell:ignore
        )
        assert body_text.strip().endswith(
            "entwickelten nur das Bild der eignen Zukunft!"  # codespell:ignore
        )

        # should not include editorial content
        assert "|" not in body_text
        assert "IX" not in body_text

    def test_getters_with_footnotes(self):
        """Test body and footnote getters for pages with footnotes."""
        tei_doc = TEIDocument.init_from_file(TEST_TEI_WITH_FOOTNOTES_FILE)

        # Test page 17 which has footnotes
        page_17 = next(
            (page for page in tei_doc.all_pages if page.number == "17"), None
        )
        assert page_17 is not None, "Page 17 not found"

        # Body assertions
        body_text = page_17.get_body_text()
        assert (
            "Der Reichthum der Gesellschaften" in body_text
        )  # codespell:ignore Reichthum,Gesellschaften
        assert "Analyse der Waare" in body_text  # codespell:ignore Waare
        assert "Karl Marx:" not in body_text
        assert "Nicholas Barbon" not in body_text

        # Footnote assertions
        footnotes = list(page_17.get_footnote_contents())
        assert len(footnotes) == 2
        assert "Karl Marx:" in footnotes[0]
        assert (
            "Zur Kritik der Politischen Oekonomie" in footnotes[0]
        )  # codespell:ignore Oekonomie
        assert "Nicholas Barbon" not in footnotes[0]
        assert "Nicholas Barbon" in footnotes[1]
        assert "Discourse on coining" in footnotes[1]
        assert "Karl Marx:" not in footnotes[1]

    def test_get_body_text(self, tei_document_fixture):
        """Test get_body_text method."""
        page = tei_document_fixture.all_pages[0]
        body_text = page.get_body_text()
        assert body_text.strip().startswith(
            "als in der ersten"  # codespell:ignore
        )

    def test_get_footnote_contents_no_footnotes(self, tei_document_fixture):
        """Test get_footnote_contents when no footnotes exist."""
        page = tei_document_fixture.all_pages[0]
        footnotes = list(page.get_footnote_contents())
        assert footnotes == []  # No footnotes in this sample

    def test_get_footnote_contents_with_footnotes(
        self, tei_document_with_footnotes_fixture
    ):
        """Test get_footnote_contents when footnotes exist."""
        page_with_footnotes = next(
            p for p in tei_document_with_footnotes_fixture.all_pages if p.number == "17"
        )
        assert page_with_footnotes is not None

        footnotes = list(page_with_footnotes.get_footnote_contents())
        assert len(footnotes) == 2
        # The footnote text includes numbering and formatting, so check for content within
        assert "Karl Marx:" in footnotes[0]
        assert "Nicholas Barbon" in footnotes[1]

    def test_is_footnote_content(self):
        """Test the is_footnote_content static method."""
        from lxml.etree import Element

        # Test direct footnote elements
        footnote_ref = Element(TEI_TAG.ref, type="footnote")
        assert TEIPage.is_footnote_content(footnote_ref) is True

        footnote_note = Element(TEI_TAG.note, type="footnote")
        assert TEIPage.is_footnote_content(footnote_note) is True

        # Test non-footnote elements
        regular_ref = Element(TEI_TAG.ref, type="citation")
        assert TEIPage.is_footnote_content(regular_ref) is False

        regular_note = Element(TEI_TAG.note, type="comment")
        assert TEIPage.is_footnote_content(regular_note) is False

        # Test element without footnote ancestors
        regular_element = Element("p")
        assert TEIPage.is_footnote_content(regular_element) is False

        # Test that the method correctly identifies direct footnote elements
        assert TEIPage.is_footnote_content(footnote_ref) is True


class TestTEIinput:
    def test_init(self):
        tei_input = TEIinput(input_file=TEST_TEI_FILE)
        assert tei_input.input_file == TEST_TEI_FILE
        # xml is parsed as tei document
        assert isinstance(tei_input.xml_doc, TEIDocument)
        # verify we have the expected pages from the fixture
        assert len(tei_input.xml_doc.pages) == 2  # non-manuscript pages

    def test_field_names(self, tmp_path: pathlib.Path):
        # includes defaults from text input and adds page number and section type
        assert TEIinput.field_names == (
            "file",
            "offset",
            "text",
            "page_number",
            "section_type",
        )

    def test_get_text(self):
        tei_input = TEIinput(input_file=TEST_TEI_FILE)
        text_result = tei_input.get_text()
        # should be a generator
        assert isinstance(text_result, Generator)
        text_result = list(text_result)
        # expect two pages, each with body text
        assert len(text_result) == 2
        # result type is dictionary
        assert all(isinstance(txt, dict) for txt in text_result)
        # check for expected contents from the actual fixture
        assert (
            "in der ersten Darstellung" in text_result[0]["text"]
        )  # codespell:ignore der,ersten,Darstellung
        assert (
            "kapitalistische Produktion" in text_result[1]["text"]  # codespell:ignore
        )
        # - page number
        assert text_result[0]["page_number"] == "12"
        assert text_result[1]["page_number"] == "13"
        # - section type (should be "text" for body content)
        assert text_result[0]["section_type"] == "text"
        assert text_result[1]["section_type"] == "text"

    def test_get_text_with_footnotes(self):
        """Test get_text with file containing footnotes across multiple pages."""
        tei_input = TEIinput(input_file=TEST_TEI_WITH_FOOTNOTES_FILE)
        text_chunks = list(tei_input.get_text())

        # Verify the overall structure - should have multiple chunks with different section types
        assert len(text_chunks) > 0

        # Check that we get both text and footnote section types
        section_types = [chunk["section_type"] for chunk in text_chunks]
        assert "text" in section_types
        assert "footnote" in section_types

        # Verify each chunk has the expected structure
        for chunk in text_chunks:
            assert "text" in chunk
            assert "page_number" in chunk
            assert "section_type" in chunk
            assert chunk["section_type"] in ["text", "footnote"]

    @patch("remarx.sentence.corpus.base_input.segment_text")
    def test_get_sentences(self, mock_segment_text: Mock, tei_document_fixture):
        """Test get_sentences with existing fixture file."""
        # Mock the segmentation to return simple test data
        mock_segment_text.side_effect = lambda text: [(0, text[:10]), (10, text[10:])]

        # Create TEIinput with a real fixture file path
        tei_input = TEIinput(input_file=TEST_TEI_FILE)
        # Override the parsed doc with our fixture
        tei_input.xml_doc = tei_document_fixture

        sentences = tei_input.get_sentences()
        # expect a generator with sentences from the fixture content
        assert isinstance(sentences, Generator)
        sentences = list(sentences)

        # Should have sentences from the fixture pages
        assert len(sentences) > 0
        assert all(isinstance(sentence, dict) for sentence in sentences)

        # Check sentence metadata
        assert sentences[0]["file"] == TEST_TEI_FILE.name

        # Get unique page numbers from sentences
        page_numbers = list({s["page_number"] for s in sentences})
        assert len(page_numbers) > 0

        # Sentence index should continue across pages
        sent_indices = [s["sent_index"] for s in sentences]
        assert sent_indices == list(range(len(sentences)))

        # Section type should be "text" for body content
        assert all(s["section_type"] == "text" for s in sentences)

        # Verify segmentation was called
        mock_segment_text.assert_called()

    @patch("remarx.sentence.corpus.base_input.segment_text")
    def test_get_sentences_with_footnotes(
        self, mock_segment_text: Mock, tei_document_with_footnotes_fixture
    ):
        """Test get_sentences maintains consecutive indexing across body and footnotes."""
        # Mock the segmentation to return simple test data
        mock_segment_text.side_effect = lambda text: [(0, text[:10]), (10, text[10:])]

        # Create TEIinput with a real fixture file path
        tei_input = TEIinput(input_file=TEST_TEI_WITH_FOOTNOTES_FILE)
        # Override the parsed doc with our fixture
        tei_input.xml_doc = tei_document_with_footnotes_fixture

        sentences = list(tei_input.get_sentences())

        # Check consecutive sentence indexing across all chunks
        sent_indices = [sentence["sent_index"] for sentence in sentences]
        assert sent_indices == list(range(len(sentences)))

        # Should have both text and footnote sections
        section_types = [sentence["section_type"] for sentence in sentences]
        assert "text" in section_types
        assert "footnote" in section_types

        # Verify segmentation was called
        mock_segment_text.assert_called()
