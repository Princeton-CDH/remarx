from remarx.sentence.corpus.tei_input import TEI_TAG


def test_tei_tag() -> None:
    # test that tei tags object is constructed as expected
    assert TEI_TAG.pb == "{http://www.tei-c.org/ns/1.0}pb"
