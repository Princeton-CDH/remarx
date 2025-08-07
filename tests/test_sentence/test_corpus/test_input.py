import pathlib
from collections.abc import Generator

from remarx.sentence.corpus.input import TextInput


def test_init(tmp_path: pathlib.Path):
    txt_file = tmp_path / "input.txt"
    txt_input = TextInput(input_file=txt_file)
    assert txt_input.input_file == txt_file


def test_file_id(tmp_path: pathlib.Path):
    txt_filename = "my_input.txt"
    txt_file = tmp_path / txt_filename
    txt_input = TextInput(input_file=txt_file)
    assert txt_input.file_id == txt_filename


def test_get_text(tmp_path: pathlib.Path):
    txt_file = tmp_path / "input.txt"
    text_contents = "placeholder content"
    txt_file.write_text(text_contents)

    txt_input = TextInput(input_file=txt_file)
    text_result = txt_input.get_text()
    # expect a generator with one item, with the content added to the file
    assert isinstance(text_result, Generator)
    text_result = list(text_result)
    assert len(text_result) == 1
    assert next(iter(text_result)) == text_contents
