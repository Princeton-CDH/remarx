import pathlib
from collections.abc import Generator
from unittest.mock import Mock, patch

import pytest
from neuxml import xmlmap

from remarx.sentence.corpus.base_input import FileInput
from remarx.sentence.corpus.tei_input import (
    TEI_TAG,
    TEIDocument,
    TEIFootnote,
    TEIinput,
    TEIParagraph,
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
        # sample tei has 2 head & 6 paragraphs
        assert len(tei_doc.text_blocks) == 8
        assert isinstance(tei_doc.text_blocks[0], TEIParagraph)
        # first paragraph is on page 12
        assert tei_doc.text_blocks[2].page_number == "12"
        # and zero footnotes
        assert len(tei_doc.footnotes) == 0

        tei_footnote_doc = TEIDocument.init_from_file(TEST_TEI_WITH_FOOTNOTES_FILE)
        # five footnotes
        assert len(tei_footnote_doc.footnotes) == 5
        assert isinstance(tei_footnote_doc.footnotes[0], TEIFootnote)

    def test_init_error(self, tmp_path: pathlib.Path):
        txtfile = tmp_path / "non-tei.txt"
        txtfile.write_text("this is not tei or xml")
        with pytest.raises(ValueError, match="Error parsing"):
            TEIDocument.init_from_file(txtfile)


cross_page_para = """<p xmlns="http://www.tei-c.org/ns/1.0">
    <lb n="41"/> und es ist <hi rendition="i">der letzte Endzweck dieses Werks das ökonomische Be-
    <pb n="14"/>
    <lb n="1"/>wegungsgesetz der modernen Gesellschaft zu enthüllen</hi> kann sie na
 </p>"""


class TestTEIParagraph:
    def test_attributes(self):
        tei_doc = TEIDocument.init_from_file(TEST_TEI_FILE)
        # first 5 paragraphs are on page 12, last on page 13
        # (skip two head elements)
        assert tei_doc.text_blocks[2].page_number == "12"
        assert tei_doc.text_blocks[6].page_number == "12"
        assert tei_doc.text_blocks[7].page_number == "13"
        # none of these have a continuing page
        assert tei_doc.text_blocks[2].continuing_page is None

    def test_get_text(self):
        tei_doc = TEIDocument.init_from_file(TEST_TEI_FILE)
        head = tei_doc.text_blocks[0]
        assert head.get_text() == "ERSTES BUCH."

        para = tei_doc.text_blocks[2]
        para_text = para.get_text()
        assert para_text.startswith(
            "als in der ersten Darstellung. Ich rathe daher dem nicht durchaus in dia-"
        )
        # middle of the paragraph includes <hi> tagged content
        assert "den Abschnitt von p. 15 (Zeile 19" in para_text
        assert para_text.endswith(" Leser dann im Text wieder fortfahren mit p. 35.")

        # second paragraph includes editorial content, which should be skipped
        para = tei_doc.text_blocks[3]
        para_text = para.get_text()
        assert para_text.startswith("Die Werthform, deren fertige")
        assert para_text.endswith("darum handelt.")
        # editorial content is skipped and doesn't introduce blank lines
        assert "Es handelt sich dabei  in der That" in para_text
        # does not set page begin offset because paragraph does not cross pages
        assert not para.page_begin_offset

    def test_get_text_skip_footnote_ref(self):
        tei_doc = TEIDocument.init_from_file(TEST_TEI_WITH_FOOTNOTES_FILE)
        para = tei_doc.text_blocks[0]
        para_text = para.get_text()
        # skips footnote reference with no line break
        assert 'Waarensammlung", die' in para_text
        assert "1)" not in para_text

    paragraph_with_formula = """<p xmlns="http://www.tei-c.org/ns/1.0" xmlns:m="http://www.w3.org/1998/Math/MathML">
     <lb n="18"/>Die englische Hochkirche z. B. verzeiht eher den Angriff auf 38 von ihren
     <lb n="19"/>39 Glaubensartikeln als auf <formula>
        <m:math>
            <m:mfrac bevelled="true"><m:mtext>1</m:mtext><m:mtext>39</m:mtext></m:mfrac>
        </m:math>
    </formula> ihres Geldeinkommens. Heutzutage ist der
    </p>"""

    def test_get_text_skip_formula(self):
        para = xmlmap.load_xmlobject_from_string(
            self.paragraph_with_formula, TEIParagraph
        )
        # should skip over math formula;
        # white space across tags doesn't get normalized (preserve character offset)
        assert "Glaubensartikeln als auf  ihres Geldeinkommens" in para.get_text()

    def test_get_text_lb_line_breaks(self):
        tei_doc = TEIDocument.init_from_file(TEST_TEI_WITH_FOOTNOTES_FILE)
        # 6th paragraph has an <lb> with no line break or space
        para = tei_doc.text_blocks[5]

        para_text = para.get_text()
        assert "Fortgang der Accumulation" in para_text
        assert "derAccumulation" not in para_text

    def test_cross_page_paragraph(self):
        para = xmlmap.load_xmlobject_from_string(cross_page_para, TEIParagraph)
        assert para.continuing_page == "14"
        para_text = para.get_text()
        assert (
            para_text
            == "und es ist der letzte Endzweck dieses Werks das ökonomische Be- "
            + "wegungsgesetz der modernen Gesellschaft zu enthüllen kann sie na"
        )
        page_begin_offset = para_text.index("wegungsgesetz")
        assert para.line_number_by_offset[page_begin_offset] == 1
        # sets page begin offset for continuing page
        assert para.page_begin_offset[page_begin_offset] == "14"


class TestTEIFootnote:
    def test_attributes(self):
        tei_doc = TEIDocument.init_from_file(TEST_TEI_WITH_FOOTNOTES_FILE)
        tei_footnote = tei_doc.footnotes[0]
        assert tei_footnote.page_number == "17"
        assert tei_footnote.line_number == 17

        tei_footnote2 = tei_doc.footnotes[1]
        assert tei_footnote2.page_number == "17"
        assert tei_footnote2.line_number == 18

    def test_get_text(self):
        tei_doc = TEIDocument.init_from_file(TEST_TEI_WITH_FOOTNOTES_FILE)
        tei_footnote = tei_doc.footnotes[0]
        footnote_text = tei_footnote.get_text()
        assert footnote_text.startswith("Karl Marx:„Zur Kritik")
        assert "1)" not in footnote_text

        tei_footnote2 = tei_doc.footnotes[1]
        footnote_text = tei_footnote2.get_text()
        assert footnote_text.startswith('"Desire implies want; ')
        # includes multiline content, text in <hi> tag
        assert (
            "in answer to Mr. Locke's Considerations etc. London 1696" in footnote_text
        )


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
        )

    def test_get_text(self):
        tei_input = TEIinput(input_file=TEST_TEI_FILE)
        text_result = tei_input.get_text()
        # should be a generator
        assert isinstance(text_result, Generator)
        text_result = list(text_result)
        # expect two heads & six paragraphs
        assert len(text_result) == 8
        # result type is dictionary
        assert all(isinstance(txt, dict) for txt in text_result)
        # check for expected contents
        # - paragraph text
        assert text_result[2]["text"].startswith("als in der ersten")
        assert text_result[3]["text"].strip().startswith("Die Werthform, deren ")
        # - page number
        assert text_result[2]["page_number"] == "12"
        assert text_result[3]["page_number"] == "12"
        assert text_result[7]["page_number"] == "13"
        # - section type = text for all
        section_type = {t["section_type"] for t in text_result}
        assert section_type == {"text"}

    def test_get_text_skip_empty(self):
        tei_input = TEIinput(input_file=TEST_TEI_FILE)
        # remove everything under the third paragraph block, resulting in empty text
        third_para = tei_input.xml_doc.text_blocks[2]
        for child in third_para.node:
            third_para.node.remove(child)
        text_result = list(tei_input.get_text())
        # paragraph with empty text should be omitted
        assert len(text_result) == 7
        # line numbers not preserved for block with no text
        assert 2 not in tei_input.text_line_numbers

    def test_get_text_with_footnotes(self):
        tei_input = TEIinput(input_file=TEST_TEI_WITH_FOOTNOTES_FILE)
        text_chunks = list(tei_input.get_text())

        # Sample includes both text and footnote content
        section_types = {chunk["section_type"] for chunk in text_chunks}
        assert section_types == {"text", "footnote"}
        # assert all body text chunks before footnotes
        num_paragraphs = len(tei_input.xml_doc.text_blocks)
        body_text_chunks = text_chunks[:num_paragraphs]
        footnote_chunks = text_chunks[num_paragraphs:]
        assert {chunk["section_type"] for chunk in body_text_chunks} == {"text"}
        assert {chunk["section_type"] for chunk in footnote_chunks} == {"footnote"}

        # Check page numbers are set correctly
        assert all("page_number" in chunk for chunk in text_chunks)
        assert all(isinstance(chunk["text"], str) for chunk in text_chunks)

    def test_get_extra_metadata(self):
        tei_input = TEIinput(input_file=TEST_TEI_WITH_FOOTNOTES_FILE)
        # line numbers populated on tei_input by get_text
        text_chunks = list(tei_input.get_text())

        para1 = text_chunks[0]
        char_index = para1["text"].index("Unsere Untersuchung")
        extra_metadata = tei_input.get_extra_metadata(para1, char_index, para1["text"])
        assert extra_metadata == {"line_number": 3}

        para2 = text_chunks[1]
        sentence_index = para2["text"].index("Die Waare ist zunächst")
        extra_metadata = tei_input.get_extra_metadata(
            para2, sentence_index, para2["text"]
        )
        assert extra_metadata == {"line_number": 5}

        # footnotes are at the end and currently include line number
        footnote_chunk = text_chunks[-1]
        assert (
            tei_input.get_extra_metadata(footnote_chunk, 4, footnote_chunk["text"])
            == {}
        )

        # if line number is already present, returns empty dict
        assert tei_input.get_extra_metadata({"line_number": 10}, 20, "text") == {}

        # if text index is not present, returns empty dict
        assert tei_input.get_extra_metadata({}, 20, "text") == {}

    def test_get_extra_metadata_page_boundary(self):
        tei_input = TEIinput(input_file=TEST_TEI_FILE)
        # append cross-page paragraph fixture to fixture document
        continuing_para = xmlmap.load_xmlobject_from_string(
            cross_page_para, TEIParagraph
        )
        tei_input.xml_doc.text_blocks[0].node.getparent().append(continuing_para.node)
        # line numbers populated on tei_input by get_text
        # _AND_ page number, but only for continuing page
        text_chunks = list(tei_input.get_text())
        continue_para_index = len(text_chunks) - 1

        # there should only be one continuing page number,
        # since only one paragraph crosses a page boundary
        assert list(tei_input.continuing_page_numbers.keys()) == [continue_para_index]

        # extra metadata should include page number override
        crosspage_text = text_chunks[-1]
        page_begin_offset = continuing_para.get_text().index("wegungsgesetz")
        extra_meta = tei_input.get_extra_metadata(
            crosspage_text, page_begin_offset, crosspage_text["text"]
        )
        # metadata should include line number AND page number
        assert extra_meta == {"page_number": "14", "line_number": 1}

    @patch("remarx.sentence.corpus.base_input.segment_text")
    def test_get_sentences(self, mock_segment_text: Mock):
        tei_input = TEIinput(input_file=TEST_TEI_FILE)
        # segment text returns a tuple of character index, sentence text
        mock_segment_text.return_value = [(0, "Aber abgesehn hiervon")]
        sentences = tei_input.get_sentences()
        # expect a generator with one item, with the content added to the file
        assert isinstance(sentences, Generator)
        sentences = list(sentences)
        assert len(sentences) == 8  # 6 paragraphs + 2 heads, one mock sentence each
        # method called once for each page of text
        assert mock_segment_text.call_count == 8
        assert all(isinstance(sentence, dict) for sentence in sentences)
        # file id set (handled by base input class)
        assert sentences[0]["file"] == TEST_TEI_FILE.name
        # page number set
        assert sentences[2]["page_number"] == "12"
        assert sentences[7]["page_number"] == "13"
        # sentence index is set and continues across pages
        sent_indices = [s["sent_index"] for s in sentences]
        assert sent_indices == list(range(8))

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
