import pathlib
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
        page_17 = next(p for p in tei_doc.all_pages if p.number == "17")

        page_text = str(page_17)

        # Should contain expected content
        assert "Der Reichthum der Gesellschaften" in page_text
        assert "Karl Marx:" in page_text
        assert "\n\n" in page_text

    def test_getters_no_footnotes(self):
        tei_doc = TEIDocument.init_from_file(TEST_TEI_FILE)
        page = tei_doc.all_pages[0]

        assert "als in der ersten" in page.get_body_text()  # codespell:ignore
        assert page.get_footnote_contents() == ""
        assert page.get_footnote_text() == ""

    def test_getters_with_footnotes(self):
        tei_doc = TEIDocument.init_from_file(TEST_TEI_WITH_FOOTNOTES_FILE)
        page_17 = next(p for p in tei_doc.all_pages if p.number == "17")

        body_text = page_17.get_body_text()
        assert "Der Reichthum der Gesellschaften" in body_text
        assert "Karl Marx:" not in body_text

        footnotes_text = page_17.get_footnote_contents()
        assert "Karl Marx:" in footnotes_text
        assert "Nicholas Barbon" in footnotes_text

    def test_is_footnote_content(self):
        from lxml.etree import Element

        footnote_ref = Element(TEI_TAG.ref, type="footnote")
        footnote_note = Element(TEI_TAG.note, type="footnote")
        regular_ref = Element(TEI_TAG.ref, type="citation")
        regular_element = Element("p")

        assert TEIPage.is_footnote_content(footnote_ref) is True
        assert TEIPage.is_footnote_content(footnote_note) is True
        assert TEIPage.is_footnote_content(regular_ref) is False
        assert TEIPage.is_footnote_content(regular_element) is False


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

    @patch("remarx.sentence.corpus.base_input.segment_text")
    def test_get_sentences(self, mock_segment_text: Mock, tei_document_fixture):
        mock_segment_text.side_effect = lambda text: [(0, text[:10]), (10, text[10:])]

        tei_input = TEIinput(input_file=TEST_TEI_FILE)
        tei_input.xml_doc = tei_document_fixture

        sentences = list(tei_input.get_sentences())
        assert len(sentences) > 0
        assert all(isinstance(sentence, dict) for sentence in sentences)
        assert sentences[0]["file"] == TEST_TEI_FILE.name

        # Check consecutive indexing
        sent_indices = [s["sent_index"] for s in sentences]
        assert sent_indices == list(range(len(sentences)))

    @patch("remarx.sentence.corpus.base_input.segment_text")
    def test_get_sentences_with_footnotes(
        self, mock_segment_text: Mock, tei_document_with_footnotes_fixture
    ):
        mock_segment_text.side_effect = lambda text: [(0, text[:10]), (10, text[10:])]

        tei_input = TEIinput(input_file=TEST_TEI_WITH_FOOTNOTES_FILE)
        tei_input.xml_doc = tei_document_with_footnotes_fixture

        sentences = list(tei_input.get_sentences())

        # Check consecutive indexing
        sent_indices = [s["sent_index"] for s in sentences]
        assert sent_indices == list(range(len(sentences)))

        # Should have both text and footnote seyuan a
        section_types = [s["section_type"] for s in sentences]
        assert "text" in section_types
        assert "footnote" in section_types
