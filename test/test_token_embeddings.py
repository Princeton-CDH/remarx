from unittest.mock import Mock, NonCallableMock

import pytest

from remarx.get_token_embeddings import (
    get_subtoken_alignment,
    get_term_spans,
    normalize_text,
)


def test_normalize_text():
    # No change should occur
    assert normalize_text(" hello world") == " hello world"
    # Leading space is added
    assert normalize_text("hello world") == " hello world"
    # Trailing white space removed
    assert normalize_text("hello world\n") == " hello world"
    # Internal whitespace sequences reduced to single space
    assert normalize_text("\t\thello   \t  world \n") == " hello world"


def test_get_term_spans():
    # Simple case
    term = "bar"
    text = "foo bar"
    assert get_term_spans(text, term) == [(4, 7)]

    # Matches term on word boundaries
    term = "foo"
    text = "The sequence 'foo' is a prefix of food."
    assert get_term_spans(text, term) == [(14, 17)]

    # Matches are case sensitive
    term = "Hello"
    text = "Hello HELLO hello... Hello."
    assert get_term_spans(text, term) == [(0, 5), (21, 26)]


def test_get_subtoken_alignment():
    # Failure case
    mock_tokenizer = NonCallableMock()
    mock_tokenizer.tokenize = Mock(return_value=["_Something", "_went", "_wrong", "."])
    err_msg = "Error: Tokenized sentence does not align with input. Try applying normalize_text first."
    with pytest.raises(ValueError, match=err_msg):
        get_subtoken_alignment(mock_tokenizer, "Misaligned sentence.", "")
    mock_tokenizer.tokenize.assert_called_once_with("Misaligned sentence.")

    # Non-error cases
    sentence = " This is a simple sentence."
    mock_tokenizer.tokenize.return_value = [
        "▁This",
        "▁is",
        "▁",
        "a",
        "▁simple",
        "▁",
        "sentence",
        ".",
    ]

    # Edge case: span doesn't overlap with sentence
    mock_tokenizer.tokenize.reset_mock()
    spans = [(30, 35)]  ## will map to nothing
    assert get_subtoken_alignment(mock_tokenizer, sentence, spans) == [[]]

    # Single, fully aligned span
    mock_tokenizer.tokenize.reset_mock()
    spans = [(18, 26)]  ## token "sentence"
    assert get_subtoken_alignment(mock_tokenizer, sentence, spans) == [[6]]
    mock_tokenizer.tokenize.assert_called_once_with(sentence)

    # Single, partially aligned span
    mock_tokenizer.tokenize.reset_mock()
    spans = [(11, 17)]  ## token "simple"
    assert get_subtoken_alignment(mock_tokenizer, sentence, spans) == [[4]]
    mock_tokenizer.tokenize.assert_called_once_with(sentence)

    # Single span aligning with multiple subtokens
    mock_tokenizer.tokenize.reset_mock()
    spans = [(6, 10)]  ## phrase "is a"
    assert get_subtoken_alignment(mock_tokenizer, sentence, spans) == [[1, 2, 3]]
    mock_tokenizer.tokenize.assert_called_once_with(sentence)

    # Multiple spans
    mock_tokenizer.tokenize.reset_mock()
    spans = [
        (1, 5),  ## token "this"
        (11, 17),  ## token "simple"
        (18, 26),  ## token "sentence"
    ]
    assert get_subtoken_alignment(mock_tokenizer, sentence, spans) == [[0], [4], [6]]
    mock_tokenizer.tokenize.assert_called_once_with(sentence)
