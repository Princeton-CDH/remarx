import pathlib
from collections.abc import Generator
from unittest.mock import Mock, patch

import pytest
from neuxml import xmlmap

from remarx.sentence.corpus.base_input import SectionType
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


@pytest.fixture
def tei_document_simple():
    """Simple TEI document with predictable text for sentence testing."""
    xml = (
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">\n'
        "  <text><body>\n"
        '    <pb n="1"/>This is a simple sentence. It has two sentences.\n'
        '    <pb n="2"/>Another page. With more content.\n'
        "  </body></text>\n"
        "</TEI>"
    )
    return xmlmap.load_xmlobject_from_string(xml, TEIDocument)


@pytest.fixture
def tei_document_simple_with_footnotes():
    """Simple TEI document with footnotes for sentence testing."""
    xml = (
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">\n'
        "  <text><body>\n"
        '    <pb n="1"/>Body text here.\n'
        '    <note type="footnote">Footnote one.</note>\n'
        '    <note type="footnote">Footnote two.</note>\n'
        "  </body></text>\n"
        "</TEI>"
    )
    return xmlmap.load_xmlobject_from_string(xml, TEIDocument)


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
        assert body_text.strip().startswith("als in der ersten")  # codespell:ignore
        assert body_text.strip().endswith(
            "entwickelten nur das Bild der eignen Zukunft!"
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
        assert "Der Reichthum der Gesellschaften" in body_text
        assert "Analyse der Waare" in body_text
        assert "Karl Marx:" not in body_text
        assert "Nicholas Barbon" not in body_text

        # Footnote assertions
        footnotes = list(page_17.get_footnote_contents())
        assert len(footnotes) == 2
        assert "Karl Marx:" in footnotes[0]
        assert "Zur Kritik der Politischen Oekonomie" in footnotes[0]
        assert "Nicholas Barbon" not in footnotes[0]
        assert "Nicholas Barbon" in footnotes[1]
        assert "Discourse on coining" in footnotes[1]
        assert "Karl Marx:" not in footnotes[1]

    def test_empty_edge_cases(
        self, tei_document_fixture, tei_document_with_footnotes_fixture
    ):
        """Test empty edge cases using fixture files (no mocks)."""

        # Use the regular fixture (no footnotes in sample)
        page = tei_document_fixture.all_pages[0]
        body_text = page.get_body_text()
        footnotes = list(page.get_footnote_contents())
        assert body_text.strip().startswith("als in der ersten")  # codespell:ignore
        assert footnotes == []  # No footnotes in this sample

        # Use the footnotes fixture to test footnote-only content
        page_with_footnotes = next(
            (
                p
                for p in tei_document_with_footnotes_fixture.all_pages
                if p.number == "17"
            ),
            None,
        )
        assert page_with_footnotes is not None

        # Test that footnotes are properly extracted
        footnotes = list(page_with_footnotes.get_footnote_contents())
        assert len(footnotes) == 2
        assert "Karl Marx:" in footnotes[0]
        assert "Nicholas Barbon" in footnotes[1]


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
        assert "in der ersten Darstellung" in text_result[0]["text"]
        assert "kapitalistische Produktion" in text_result[1]["text"]
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

        # Find page 17 chunks (body text + 2 separate footnotes)
        page_17_chunks = [
            chunk for chunk in text_chunks if chunk["page_number"] == "17"
        ]
        assert len(page_17_chunks) == 3

        # Body text chunk
        body_chunk = page_17_chunks[0]
        assert body_chunk["section_type"] == SectionType.TEXT.value
        assert "Der Reichthum der Gesellschaften" in body_chunk["text"]

        # First footnote chunk
        footnote1_chunk = page_17_chunks[1]
        assert footnote1_chunk["section_type"] == SectionType.FOOTNOTE.value
        assert "Karl Marx:" in footnote1_chunk["text"]
        assert "Nicholas Barbon" not in footnote1_chunk["text"]

        # Second footnote chunk
        footnote2_chunk = page_17_chunks[2]
        assert footnote2_chunk["section_type"] == SectionType.FOOTNOTE.value
        # Page 18 has two non-spanning footnotes
        page_18_chunks = [
            chunk for chunk in text_chunks if chunk["page_number"] == "18"
        ]
        assert len(page_18_chunks) == 3
        # One body chunk and two footnote chunks
        assert page_18_chunks[0]["section_type"] == SectionType.TEXT.value
        assert page_18_chunks[1]["section_type"] == SectionType.FOOTNOTE.value
        assert page_18_chunks[2]["section_type"] == SectionType.FOOTNOTE.value

        # Page 19 has body + one footnote
        page_19_chunks = [
            chunk for chunk in text_chunks if chunk["page_number"] == "19"
        ]
        assert len(page_19_chunks) == 2
        assert page_19_chunks[0]["section_type"] == SectionType.TEXT.value
        assert page_19_chunks[1]["section_type"] == SectionType.FOOTNOTE.value
        assert "Nicholas Barbon" in footnote2_chunk["text"]
        assert "Karl Marx:" not in footnote2_chunk["text"]

    @patch("remarx.sentence.corpus.base_input.segment_text")
    def test_get_sentences(self, mock_segment_text: Mock):
        # segment text returns a tuple of character index, sentence text
        mock_segment_text.return_value = [(0, "Mock sentence")]

        tei_input = TEIinput(input_file=TEST_TEI_FILE)
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

    @patch("remarx.sentence.corpus.base_input.segment_text")
    def test_get_sentences_with_footnotes(self, mock_segment_text: Mock):
        """Test get_sentences maintains consecutive indexing across body and footnotes."""
        mock_segment_text.return_value = [(0, "Mock sentence.")]

        tei_input = TEIinput(input_file=TEST_TEI_WITH_FOOTNOTES_FILE)
        sentences = list(tei_input.get_sentences())

        # Check consecutive sentence indexing across all chunks
        sent_indices = [sentence["sent_index"] for sentence in sentences]
        assert sent_indices == list(range(len(sentences)))

        # Should have both text and footnote sections
        section_types = [sentence["section_type"] for sentence in sentences]
        assert "text" in section_types
        assert "footnote" in section_types
