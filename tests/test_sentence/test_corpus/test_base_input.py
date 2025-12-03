import pathlib
from unittest.mock import patch

import pytest

from remarx.sentence.corpus.base_input import FileInput


def test_subclasses():
    # check that expected input subclasses are found
    subclass_names = [cls.__name__ for cls in FileInput.subclasses()]
    # NOTE: that we use names here rather than importing, to
    # confirm subclasses are found without a direct import
    for input_cls_name in ["TextInput", "TEIinput", "ALTOInput"]:
        assert input_cls_name in subclass_names


def test_init(tmp_path: pathlib.Path):
    txt_file = tmp_path / "input.txt"
    txt_input = FileInput(input_file=txt_file)
    assert txt_input.input_file == txt_file


def test_file_name(tmp_path: pathlib.Path):
    txt_filename = "my_input.txt"
    txt_file = tmp_path / txt_filename
    txt_input = FileInput(input_file=txt_file)
    assert txt_input.file_name == txt_filename


def test_file_name_override(tmp_path: pathlib.Path):
    real_txt_filename = "my_input.txt"
    txt_file = tmp_path / "tmp_abc_input_foo.txt"
    txt_input = FileInput(input_file=txt_file, filename_override=real_txt_filename)
    assert txt_input.file_name == real_txt_filename


def test_field_names(tmp_path: pathlib.Path):
    assert FileInput.field_names == ("sent_id", "file", "sent_index", "text")


def test_supported_types():
    # check for expected supported types
    # NOTE: checking directly to avoid importing input classes
    assert set(FileInput.supported_types()) == {".txt", ".xml", ".zip"}


def test_get_text(tmp_path: pathlib.Path):
    # get text is not implemented in the base class
    txt_file = tmp_path / "test.txt"
    base_input = FileInput(input_file=txt_file)
    with pytest.raises(NotImplementedError):
        base_input.get_text()


@patch("remarx.sentence.corpus.base_input.segment_text")
@patch.object(FileInput, "get_text")
def test_get_sentences(mock_text, mock_segment, tmp_path: pathlib.Path):
    mock_segment.side_effect = lambda x: [(0, x)]
    mock_text.return_value = [{"id": i, "text": f"s{i}"} for i in range(3)]
    txt_file = tmp_path / "test.txt"
    base_input = FileInput(input_file=txt_file)

    results = list(base_input.get_sentences())
    assert len(results) == 3
    for i in range(3):
        assert results[i] == {
            "id": i,
            "text": f"s{i}",
            "file": "test.txt",
            "sent_index": i,
            "sent_id": f"test.txt:{i}",
        }


def test_create_txt(tmp_path: pathlib.Path):
    from remarx.sentence.corpus.text_input import TextInput

    txt_file = tmp_path / "input.txt"
    txt_input = FileInput.create(input_file=txt_file)
    assert isinstance(txt_input, TextInput)


def test_create_exts(tmp_path: pathlib.Path):
    from remarx.sentence.corpus.text_input import TextInput

    txt_file = tmp_path / "upper.TXT"
    txt_input = FileInput.create(input_file=txt_file)
    assert isinstance(txt_input, TextInput)

    txt_file = tmp_path / "mixed.TxT"
    txt_input = FileInput.create(input_file=txt_file)
    assert isinstance(txt_input, TextInput)


def test_create_filename_override(tmp_path: pathlib.Path):
    from remarx.sentence.corpus.text_input import TextInput

    txt_file = tmp_path / "tmp_foo_bar_input.txt"
    real_filename = "input.txt"
    txt_input = FileInput.create(input_file=txt_file, filename_override=real_filename)
    assert isinstance(txt_input, TextInput)
    assert txt_input.file_name == real_filename


@patch("remarx.sentence.corpus.tei_input.TEIDocument")
def test_create_tei(mock_tei_doc, tmp_path: pathlib.Path):
    from remarx.sentence.corpus.tei_input import TEIinput

    xml_input_file = tmp_path / "input.xml"
    xml_input = FileInput.create(input_file=xml_input_file)
    assert isinstance(xml_input, TEIinput)
    mock_tei_doc.init_from_file.assert_called_with(xml_input_file)


def test_create_alto(tmp_path: pathlib.Path):
    from remarx.sentence.corpus.alto_input import ALTOInput

    zip_input_file = tmp_path / "input.zip"
    zip_input_file.touch()
    zip_input = FileInput.create(input_file=zip_input_file)
    assert isinstance(zip_input, ALTOInput)


def test_create_unsupported(tmp_path: pathlib.Path):
    test_file = tmp_path / "input.test"
    with pytest.raises(
        ValueError,
        match="\\.test is not a supported input type \\(must be one of \\.txt, \\.xml, \\.zip\\)",
    ):
        FileInput.create(input_file=test_file)
