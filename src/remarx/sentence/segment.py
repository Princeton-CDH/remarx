"""
Sentence segmentation utilities for text processing.

This utility module provides functionality to segment text into sentences and
return character-indexed sentence pairs.
"""

import stanza


def segment_text(text: str, language: str = "de") -> list[tuple[int, str]]:
    """
    Segment text into sentences with character indices.
    Takes a string of text and returns a list of tuples containing the character
    index where each sentence starts and the sentence text itself.

    Example:
        >>> text = "This is sentence one. This is sentence two."
        >>> sentences = segment_text(text, language="en")
        >>> sentences
        [(0, 'This is sentence one.'), (22, 'This is sentence two.')]
    """
    # Initialize the NLP pipeline for sentence segmentation
    # Use minimal processors (tokenize) for sentence segmentation only
    segmenter = stanza.Pipeline(lang=language, processors="tokenize")

    # Segment the plain text
    processed_doc = segmenter(text)

    # Extract sentences with character-level indices
    sentences = []
    for sentence in processed_doc.sentences:
        # Get the character start position of the sentence
        char_start = sentence.tokens[0].start_char
        # Get the sentence text
        sentence_text = sentence.text
        sentences.append((char_start, sentence_text))

    return sentences
