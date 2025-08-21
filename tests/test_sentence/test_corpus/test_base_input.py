import pathlib
from unittest.mock import patch

import pytest

from remarx.sentence.corpus.base_input import FileInput
from remarx.sentence.corpus.tei_input import TEIinput
from remarx.sentence.corpus.text_input import TextInput


class MyTestInput(FileInput):
    file_type = ".foo"
    pass


FileInput.register_input(MyTestInput)

# expected input classes, real and test
input_classes = [TextInput, TEIinput, MyTestInput]


def test_register_input():
    assert ".foo" in FileInput._input_classes
    assert FileInput._input_classes[".foo"] == MyTestInput


def test_default_registration():
    # check that expected input classes are available
    for input_cls in input_classes:
        assert input_cls.file_type in FileInput._input_classes
        assert FileInput._input_classes[input_cls.file_type] == input_cls


def test_supported_types():
    # check for expected supported types
    expected_types = {input_cls.file_type for input_cls in input_classes}
    assert set(FileInput.supported_types()) == expected_types


def test_get_text(tmp_path: pathlib.Path):
    # get text is not implemented in the base class
    txt_file = tmp_path / "test.txt"
    base_input = FileInput(input_file=txt_file)
    with pytest.raises(NotImplementedError):
        base_input.get_text()


def test_init_txt(tmp_path: pathlib.Path):
    txt_file = tmp_path / "input.txt"
    txt_input = FileInput.init(input_file=txt_file)
    assert isinstance(txt_input, TextInput)


@patch("remarx.sentence.corpus.tei_input.TEIDocument")
def test_init_tei(mock_tei_doc, tmp_path: pathlib.Path):
    xml_input_file = tmp_path / "input.xml"
    xml_input = FileInput.init(input_file=xml_input_file)
    assert isinstance(xml_input, TEIinput)
    mock_tei_doc.init_from_file.assert_called_with(xml_input_file)


def test_init_unsupported(tmp_path: pathlib.Path):
    test_file = tmp_path / "input.test"
    with pytest.raises(ValueError, match="not a supported input type"):
        FileInput.init(input_file=test_file)
