"""
Provides functionality to break down input text into individual
sentences and return them as tuples containing the character index where each
sentence begins and the sentence text itself.
"""

import stanza
from stanza import DownloadMethod


def segment_text(text: str, language: str = "de") -> list[tuple[int, str]]:
    """
    Segment a string of text into sentences with character indices.

    :param text: Input text to be segmented into sentences
    :param language: Language code for the Stanza pipeline
    :return: List of tuples where each tuple contains (start_char_index, sentence_text)
    """
    # Initialize the NLP pipeline for sentence segmentation
    # Use minimal processors (tokenize) for sentence segmentation only
    segmenter = stanza.Pipeline(
        lang=language,
        processors="tokenize",
        download_method=DownloadMethod.REUSE_RESOURCES,
    )

    processed_doc = segmenter(text)

    # Extract sentences with character-level indices
    return [
        (sentence.tokens[0].start_char, sentence.text)
        for sentence in processed_doc.sentences
    ]
