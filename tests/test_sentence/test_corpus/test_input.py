import pathlib
from collections.abc import Generator
from unittest.mock import Mock, patch

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


def test_field_names(tmp_path: pathlib.Path):
    txt_file = tmp_path / "input.txt"
    txt_input = TextInput(input_file=txt_file)
    assert txt_input.field_names() == ["file_id", "offset", "text"]


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


@patch("remarx.sentence.corpus.input.segment_text")
def test_get_sentences(mock_segment_text: Mock, tmp_path: pathlib.Path):
    txt_file = tmp_path / "input.txt"
    text_content = "more placeholder content"
    txt_file.write_text(text_content)
    # segment text returns a tuple of character index, sentence text
    mock_segment_text.return_value = [(0, text_content)]

    txt_input = TextInput(input_file=txt_file)
    sentences = txt_input.get_sentences()
    # expect a generator with one item, with the content added to the file
    assert isinstance(sentences, Generator)
    sentences = list(sentences)
    assert len(sentences) == 1
    first_sentence = sentences[0]
    assert isinstance(first_sentence, dict)
    assert first_sentence["text"] == text_content
    assert first_sentence["file_id"] == txt_file.name
