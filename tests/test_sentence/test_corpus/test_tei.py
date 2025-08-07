import pathlib

import pytest

from remarx.sentence.corpus.tei_input import TEI_TAG, TEIDocument, TEIPage

FIXTURE_DIR = pathlib.Path(__file__).parent / "fixtures"
TEST_TEI_FILE = FIXTURE_DIR / "sample_tei.xml"


def test_tei_tag():
    # test that tei tags object is  nstructed as expected
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
        # TODO: should not include footnote content
