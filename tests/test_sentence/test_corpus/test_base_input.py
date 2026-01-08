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
    # Use valid sentences that won't be filtered out (3+ words)
    mock_segment.side_effect = lambda x: [(0, x)]
    mock_text.return_value = [
        {"id": i, "text": f"This is sentence {i} with enough words."} for i in range(3)
    ]
    txt_file = tmp_path / "test.txt"
    base_input = FileInput(input_file=txt_file)

    results = list(base_input.get_sentences())
    assert len(results) == 3
    for i in range(3):
        assert results[i] == {
            "id": i,
            "text": f"This is sentence {i} with enough words.",
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


class TestSentenceValidation:
    """Test sentence filtering functionality."""

    def test_punctuation_only_sentences_dropped(self, tmp_path: pathlib.Path):
        """Test that punctuation-only sentences are dropped."""
        txt_file = tmp_path / "test.txt"
        base_input = FileInput(input_file=txt_file)

        # Test various punctuation-only sentences
        assert not base_input.include_sentence("...")
        assert not base_input.include_sentence("!!!")
        assert not base_input.include_sentence("?")
        assert not base_input.include_sentence("—")
        assert not base_input.include_sentence(".")

    def test_single_word_sentences_dropped(self, tmp_path: pathlib.Path):
        """Test that single-word sentences are dropped."""
        txt_file = tmp_path / "test.txt"
        base_input = FileInput(input_file=txt_file)

        assert not base_input.include_sentence("Ja.")
        assert not base_input.include_sentence("Nein")
        assert not base_input.include_sentence("Hello")
        assert not base_input.include_sentence("123")

    def test_two_word_sentences_dropped(self, tmp_path: pathlib.Path):
        """Test that two-word sentences are dropped."""
        txt_file = tmp_path / "test.txt"
        base_input = FileInput(input_file=txt_file)

        assert not base_input.include_sentence("Hello world")
        assert not base_input.include_sentence("Good morning")
        assert not base_input.include_sentence("One two")

    def test_three_plus_word_sentences_kept(self, tmp_path: pathlib.Path):
        """Test that sentences with 3+ words are kept."""
        txt_file = tmp_path / "test.txt"
        base_input = FileInput(input_file=txt_file)

        assert base_input.include_sentence("This is a test sentence.")
        assert base_input.include_sentence("Hello world, how are you?")
        assert base_input.include_sentence("The quick brown fox jumps.")

    def test_sentences_with_numbers_kept_if_enough_words(self, tmp_path: pathlib.Path):
        """Test that sentences with numbers are treated as valid words."""
        txt_file = tmp_path / "test.txt"
        base_input = FileInput(input_file=txt_file)

        # Three words with numbers should be kept
        assert base_input.include_sentence("The year 2023 was")
        assert base_input.include_sentence("Page 1 of 10")

        # But still drop if only 1-2 valid tokens
        assert not base_input.include_sentence("2023")
        assert not base_input.include_sentence("Page 1")

    def test_sentences_with_mixed_alphanumeric_kept(self, tmp_path: pathlib.Path):
        """Test sentences with mixed alphanumeric content."""
        txt_file = tmp_path / "test.txt"
        base_input = FileInput(input_file=txt_file)

        assert base_input.include_sentence("The 2nd amendment is")
        assert base_input.include_sentence("Chapter 3 discusses the")

    def test_exclude_p_abbreviation(self, tmp_path: pathlib.Path):
        """Sentences consisting only of punctuation/digits and 'p' should be dropped."""
        txt_file = tmp_path / "test.txt"
        base_input = FileInput(input_file=txt_file)

        assert not base_input.include_sentence("1862, p. 56.)")
        assert not base_input.include_sentence("1848“, p. 113.)")
        assert not base_input.include_sentence("p. 56, 57.")

        # Test that sentences with 'p' in valid sentences are included
        assert base_input.include_sentence("The word p should be included.")
        assert base_input.include_sentence("Please pass the salt.")
        assert base_input.include_sentence("The letter p appears here.")


@patch("remarx.sentence.corpus.base_input.segment_text")
@patch.object(FileInput, "get_text")
def test_get_sentences_filters_invalid_sentences(
    mock_text, mock_segment, tmp_path: pathlib.Path, caplog
):
    """Test that get_sentences filters out invalid sentences."""
    # Mock segment_text to return various sentences
    mock_segment.side_effect = lambda x: [
        (0, "Short."),  # 1 word - should be dropped
        (8, "Two words."),  # 2 words - should be dropped
        (20, "..."),  # punctuation only - should be dropped
        (24, "This is a valid sentence."),  # 5 words - should be kept
        (52, "Another good sentence here."),  # 4 words - should be kept
    ]
    mock_text.return_value = [{"text": "Mock text chunk"}]

    txt_file = tmp_path / "test.txt"
    base_input = FileInput(input_file=txt_file)

    with caplog.at_level("DEBUG"):
        results = list(base_input.get_sentences())

    # Should only get the 2 valid sentences
    assert len(results) == 2
    assert results[0]["text"] == "This is a valid sentence."
    assert results[0]["sent_index"] == 0
    assert results[1]["text"] == "Another good sentence here."
    assert results[1]["sent_index"] == 1

    # Check that a summary info message was logged for omitted sentences
    assert "Omitted 3 short/punct-only sentences" in caplog.text
