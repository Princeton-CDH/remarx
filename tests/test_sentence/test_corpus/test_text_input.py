import pathlib
from collections.abc import Generator
from unittest.mock import Mock, patch

from remarx.sentence.corpus.base_input import FileInput
from remarx.sentence.corpus.text_input import TextInput


def test_init(tmp_path: pathlib.Path):
    txt_file = tmp_path / "input.txt"
    txt_input = TextInput(input_file=txt_file)
    assert txt_input.input_file == txt_file


def test_file_name(tmp_path: pathlib.Path):
    txt_filename = "my_input.txt"
    txt_file = tmp_path / txt_filename
    txt_input = TextInput(input_file=txt_file)
    assert txt_input.file_name == txt_filename


def test_field_names(tmp_path: pathlib.Path):
    assert TextInput.field_names == FileInput.field_names


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
    first_result = next(iter(text_result))
    assert isinstance(first_result, dict)
    # text content matches expected results
    assert first_result["text"] == text_contents
    # dict should only includes text
    assert list(first_result.keys()) == ["text"]


def simple_segmenter(text: str):
    # for testing purposes, dummy segmenter that splits input text in half
    half_text_len = int(len(text) / 2)
    # segment text returns a generator of tuple of character index, sentence text
    return ((0, text[:half_text_len]), (half_text_len, text[half_text_len:]))


@patch("remarx.sentence.corpus.base_input.segment_text")
def test_get_sentences(mock_segment_text: Mock, tmp_path: pathlib.Path):
    txt_file = tmp_path / "input.txt"
    text_content = "more placeholder content"
    txt_file.write_text(text_content)
    # call simple segmenter to split input text in two
    mock_segment_text.side_effect = simple_segmenter

    txt_input = TextInput(input_file=txt_file)
    sentences = txt_input.get_sentences()
    # expect a generator with two item, with the content added to the file
    assert isinstance(sentences, Generator)
    # consume the generator
    sentences = list(sentences)
    assert len(sentences) == 2

    # expect segmentation method to be called only once
    mock_segment_text.assert_called_once()

    first_sentence = sentences[0]
    assert isinstance(first_sentence, dict)
    # should not be the full text content
    assert first_sentence["text"] != text_content
    # should _start_ with the text content
    assert first_sentence["text"].startswith(text_content[:5])
    assert first_sentence["file"] == txt_file.name
    assert first_sentence["sent_index"] == 0

    second_sentence = sentences[1]
    # should not be the full text content
    assert second_sentence["text"] != text_content
    # but should _end_ with the text content
    assert second_sentence["text"].endswith(text_content[-5:])
    assert second_sentence["file"] == txt_file.name
