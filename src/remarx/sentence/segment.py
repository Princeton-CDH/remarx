"""
Provides functionality to break down input text into individual
sentences and return them as tuples containing the character index where each
sentence begins and the sentence text itself.
"""

import stanza


def segment_text(text: str, language: str = "de") -> list[tuple[int, str]]:
    """
    Segment text into sentences with character indices.
    Takes a string of text and returns a list of tuples containing the character
    index where each sentence starts and the sentence text itself.

    Example:
        ```python
        >>> text = "This is sentence one. This is sentence two."
        >>> sentences = segment_text(text, language="en")
        >>> sentences
        [(0, 'This is sentence one.'), (22, 'This is sentence two.')]
        ```
    """
    # Initialize the NLP pipeline for sentence segmentation
    # Use minimal processors (tokenize) for sentence segmentation only
    segmenter = stanza.Pipeline(lang=language, processors="tokenize")

    processed_doc = segmenter(text)

    # Extract sentences with character-level indices
    return [
        (sentence.tokens[0].start_char, sentence.text)
        for sentence in processed_doc.sentences
    ]
