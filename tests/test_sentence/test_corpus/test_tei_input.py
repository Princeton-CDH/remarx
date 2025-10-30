import pathlib
from collections.abc import Generator
from unittest.mock import Mock, patch

import pytest
from lxml.etree import Element

from remarx.sentence.corpus.base_input import FileInput, SectionType
from remarx.sentence.corpus.tei_input import (
    TEI_TAG,
    ParagraphChunk,
    TEIDocument,
    TEIinput,
    TEIPage,
)

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

    def test_pages_by_number(self):
        tei_doc = TEIDocument.init_from_file(TEST_TEI_FILE)
        assert isinstance(tei_doc.pages_by_number, dict)
        assert list(tei_doc.pages_by_number.values()) == tei_doc.pages
        assert list(tei_doc.pages_by_number.keys()) == [p.number for p in tei_doc.pages]
        first_page = tei_doc.pages[0]
        assert tei_doc.pages_by_number[first_page.number] == first_page


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

    def test_get_body_text_line_numbers(self):
        tei_doc = TEIDocument.init_from_file(TEST_TEI_WITH_FOOTNOTES_FILE)
        page_17 = next(p for p in tei_doc.pages if p.number == "17")

        body_text = page_17.get_body_text()
        first_line_idx = body_text.index("Der Reichthum der Gesellschaften")
        second_line_idx = body_text.index("Die Waare ist zunächst")  # codespell:ignore

        assert page_17.get_body_text_line_number(first_line_idx) == 1
        assert page_17.get_body_text_line_number(second_line_idx) == 5
        assert page_17.get_body_text_line_number(second_line_idx + 10) == 5

    def test_get_body_text_line_number_without_cached_data(self):
        """Test get_body_text_line_number when line_number_by_offset doesn't exist yet."""
        tei_doc = TEIDocument.init_from_file(TEST_TEI_WITH_FOOTNOTES_FILE)
        page_17 = next(p for p in tei_doc.pages if p.number == "17")

        # Ensure the page doesn't have cached line number data
        assert not hasattr(page_17, "line_number_by_offset")

        # This should trigger the hasattr check and call get_body_text()
        line_number = page_17.get_body_text_line_number(0)

        # After the call, the attribute should be set
        assert hasattr(page_17, "line_number_by_offset")
        assert line_number == 1

    def test_get_body_text_multiple_lb_line_breaks(self):
        tei_doc = TEIDocument.init_from_file(TEST_TEI_WITH_FOOTNOTES_FILE)
        page_21 = next(p for p in tei_doc.pages if p.number == "21")

        body_text = page_21.get_body_text()

        assert "Fortgang der\nAccumulation" in body_text
        assert "derAccumulation" not in body_text

    def test_get_body_text_line_numbers_without_any_lb(self):
        tei_doc = TEIDocument.init_from_file(TEST_TEI_WITH_FOOTNOTES_FILE)
        page_22 = next(p for p in tei_doc.pages if p.number == "22")

        body_text = page_22.get_body_text()
        assert body_text.startswith("Eine Seite ohne markierte Zeilenumbrüche.")
        assert page_22.line_number_by_offset == {}
        assert page_22.get_body_text_line_number(0) is None

    def test_get_body_text_line_numbers_with_inline_markup(self):
        tei_doc = TEIDocument.init_from_file(TEST_TEI_WITH_FOOTNOTES_FILE)
        page_21 = next(p for p in tei_doc.pages if p.number == "21")

        body_text = page_21.get_body_text()

        inline_start = body_text.index("Schiedensten Proportionen")
        assert body_text[:inline_start].endswith("\n")
        assert page_21.get_body_text_line_number(inline_start) == 31

        assert "Dennoch bleibt sein\nTauschwerth" in body_text
        second_block_start = body_text.index("Dennoch bleibt sein\nTauschwerth")
        tauschwerth_idx = second_block_start + len("Dennoch bleibt sein\n")
        assert page_21.get_body_text_line_number(tauschwerth_idx) == 34
        unveraendert_idx = body_text.index("unverändert", tauschwerth_idx)
        assert page_21.get_body_text_line_number(unveraendert_idx) == 34

        # Ensure blank <lb/> entries still add newline placeholders and line mappings.
        assert "\n\nLeerzeile als separates Beispiel." in body_text  # codespell:ignore
        leerzeile_idx = body_text.index(
            "Leerzeile als separates Beispiel."  # codespell:ignore
        )  # codespell:ignore
        assert page_21.get_body_text_line_number(leerzeile_idx) == 39
        assert 38 in page_21.line_number_by_offset.values()

    def test_get_footnote_text_with_footnotes(self):
        tei_doc = TEIDocument.init_from_file(TEST_TEI_WITH_FOOTNOTES_FILE)
        page_17 = next(p for p in tei_doc.all_pages if p.number == "17")

        footnote_text = page_17.get_footnote_text()
        assert footnote_text.startswith("Karl Marx:")
        assert "Nicholas Barbon" in footnote_text
        assert (
            "Der Reichthum der Gesellschaften" not in footnote_text
        )  # Body text should be excluded

    def test_get_footnote_line_numbers(self):
        tei_doc = TEIDocument.init_from_file(TEST_TEI_WITH_FOOTNOTES_FILE)
        page_17 = next(p for p in tei_doc.pages if p.number == "17")

        footnotes = list(page_17.get_page_footnotes())
        # returns footnote xmlobject, which has a line number attribute
        assert footnotes[0].line_number == 17
        assert footnotes[1].line_number == 18
        assert footnotes[0].label.strip().startswith("1")
        assert footnotes[0].text.startswith("Karl Marx:")

    def test_get_footnote_text_delimiter(self):
        # Test that footnotes are properly separated by double newlines
        tei_doc = TEIDocument.init_from_file(TEST_TEI_WITH_FOOTNOTES_FILE)
        page_17 = next(p for p in tei_doc.all_pages if p.number == "17")

        footnote_text = page_17.get_footnote_text()
        # Check that double newlines are present between footnotes
        # The fixture should have multiple footnotes to test this properly
        assert "\n\n" in footnote_text

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

    def test_get_body_text_line_numbers_missing_lb_number(self):
        tei_doc = TEIDocument.init_from_file(TEST_TEI_WITH_FOOTNOTES_FILE)
        page_20 = next(p for p in tei_doc.pages if p.number == "20")

        body_text = page_20.get_body_text()
        assert "Erste Umschlagseite der Erstausgabe" in body_text, (
            "Fixture text missing expected caption content"
        )

        # No numbered line marker before the first characters, so None is expected
        assert page_20.get_body_text_line_number(0) is None

    def test_iter_body_paragraphs_groups_text(self):
        tei_doc = TEIDocument.init_from_file(TEST_TEI_FILE)
        page = tei_doc.pages[0]

        chunks = list(page.iter_body_paragraphs())
        assert len(chunks) == 5
        assert all(isinstance(chunk, ParagraphChunk) for chunk in chunks)
        assert chunks[0].text.startswith(
            "als in der ersten Darstellung."  # codespell:ignore
        )  # codespell:ignore
        # Ensure editorial markers are skipped
        assert all("|" not in chunk.text for chunk in chunks)
        assert all(chunk.continued is False for chunk in chunks)

    def test_find_preceding_lb(self):
        tei_doc = TEIDocument.init_from_file(TEST_TEI_WITH_FOOTNOTES_FILE)
        # use xpath to get known elements from fixture doc for testing
        # all xpaths need tei namespace declared so we can use t: prefix
        tei_ns = {"namespaces": TEIDocument.ROOT_NAMESPACES}

        # lb 31 has an immediately preceding hi tag
        linebegin31 = tei_doc.node.xpath('.//t:lb[@n="31"]', **tei_ns)[0]
        inline_el = tei_doc.node.xpath(
            './/t:hi[preceding-sibling::t:lb[@n="31"]]', **tei_ns
        )[0]
        assert TEIPage.find_preceding_lb(inline_el) == linebegin31
        # test nested inline el
        linebegin2 = tei_doc.node.xpath('.//t:lb[@n="2"]', **tei_ns)[0]
        nested_inline_el = tei_doc.node.xpath(
            './/t:ref[@target="fn1-1"]/t:hi', **tei_ns
        )[0]
        assert TEIPage.find_preceding_lb(nested_inline_el) == linebegin2
        # no preceding lb should return none
        pagebegin2 = tei_doc.node.xpath('.//t:pb[@n="17"]', **tei_ns)[0]
        assert TEIPage.find_preceding_lb(pagebegin2) is None


class TestTEIinput:
    def test_init(self):
        tei_input = TEIinput(input_file=TEST_TEI_FILE)
        assert tei_input.input_file == TEST_TEI_FILE
        # xml is parsed as tei document
        assert isinstance(tei_input.xml_doc, TEIDocument)

    def test_field_names(self):
        # includes defaults from text input and adds page number, section type, and line number
        assert TEIinput.field_names == (
            *FileInput.field_names,
            "page_number",
            "section_type",
            "line_number",
            "continued",
        )

    def test_get_text(self):
        tei_input = TEIinput(input_file=TEST_TEI_FILE)
        text_result = tei_input.get_text()
        # should be a generator
        assert isinstance(text_result, Generator)
        text_result = list(text_result)
        assert all(isinstance(txt, dict) for txt in text_result)
        first_chunk = text_result[0]
        assert first_chunk["section_type"] == SectionType.TEXT.value
        assert first_chunk["page_number"] == "12"
        assert first_chunk["text"].startswith(
            "als in der ersten Darstellung."  # codespell:ignore
        )  # codespell:ignore
        assert "continued" in first_chunk
        text_chunks = [
            chunk
            for chunk in text_result
            if chunk["section_type"] == SectionType.TEXT.value
        ]
        assert text_chunks[-1]["page_number"] == "13"
        assert text_chunks[-1]["text"].startswith(
            "Aber abgesehn hiervon"
        )  # codespell:ignore

    def test_get_text_with_footnotes(self):
        tei_input = TEIinput(input_file=TEST_TEI_WITH_FOOTNOTES_FILE)
        text_chunks = list(tei_input.get_text())

        # Should get both text and footnote chunks for each page
        section_types = [chunk["section_type"] for chunk in text_chunks]
        assert "text" in section_types
        assert "footnote" in section_types
        assert all("continued" in chunk for chunk in text_chunks)

        # Check page numbers are set correctly
        assert all("page_number" in chunk for chunk in text_chunks)
        assert all(isinstance(chunk["text"], str) for chunk in text_chunks)
        footnote_ref_chunk = next(
            chunk
            for chunk in text_chunks
            if chunk["section_type"] == SectionType.TEXT.value
            and chunk["page_number"] == "17"
        )
        assert (
            "ungeheure Waarensammlung" in footnote_ref_chunk["text"]
        )  # codespell:ignore
        assert (
            'ungeheure Waarensammlung"' in footnote_ref_chunk["text"]
        )  # codespell:ignore

    def test_get_extra_metadata_line_numbers(self):
        tei_input = TEIinput(input_file=TEST_TEI_WITH_FOOTNOTES_FILE)
        text_chunks = list(tei_input.get_text())

        body_chunk = next(
            chunk
            for chunk in text_chunks
            if chunk["section_type"] == SectionType.TEXT.value
            and chunk["page_number"] == "17"
            and "Die Waare ist zunächst" in chunk["text"]  # codespell:ignore
        )
        body_idx = body_chunk["text"].index(
            "Die Waare ist zunächst"  # codespell:ignore
        )  # codespell:ignore
        body_metadata = tei_input.get_extra_metadata(
            body_chunk, body_idx, body_chunk["text"]
        )
        assert body_metadata["line_number"] == 5

        footnote_chunk = next(
            chunk
            for chunk in text_chunks
            if chunk["section_type"] == SectionType.FOOTNOTE.value
            and chunk["page_number"] == "17"
            and chunk["text"].startswith("Karl Marx:")
        )
        footnote_metadata = tei_input.get_extra_metadata(
            footnote_chunk, 4, footnote_chunk["text"]
        )
        assert footnote_metadata["line_number"] == 17

    def test_get_extra_metadata_missing_page_returns_none(self):
        tei_input = TEIinput(input_file=TEST_TEI_FILE)
        metadata = tei_input.get_extra_metadata(
            {
                "page_number": "999",
                "section_type": SectionType.TEXT.value,
                "text": "",
            },
            0,
            "",
        )
        assert metadata["line_number"] is None

    @patch("remarx.sentence.corpus.tei_input.segment_text")
    def test_get_sentences(self, mock_segment_text: Mock):
        chunk_counter_input = TEIinput(input_file=TEST_TEI_FILE)
        chunk_count = len(list(chunk_counter_input.get_text()))

        tei_input = TEIinput(input_file=TEST_TEI_FILE)
        mock_segment_text.return_value = [(0, "Aber abgesehn hiervon")]
        sentences = list(tei_input.get_sentences())

        assert mock_segment_text.call_count == chunk_count
        assert all(isinstance(sentence, dict) for sentence in sentences)
        assert sentences[0]["file"] == TEST_TEI_FILE.name
        assert sentences[0]["page_number"] == "12"
        assert sentences[0]["sent_index"] == 0

    @patch("remarx.sentence.corpus.tei_input.segment_text")
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
