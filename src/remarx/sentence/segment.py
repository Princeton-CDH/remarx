"""
Provides functionality to break down input text into individual
sentences and return them as tuples containing the character index where each
sentence begins and the sentence text itself.
"""

import spacy
from spacy.cli import download


def segment_text(text: str, model: str = "de_core_news_sm") -> list[tuple[int, str]]:
    """
    Segment a string of text into sentences with character indices.

    Automatically downloads the spaCy model on first use if it is not installed.

    :param text: Input text to be segmented into sentences
    :param model: spaCy model name, defaulted to "de_core_news_sm"
    :return: List of tuples where each tuple contains (start_char_index, sentence_text)
    """

    try:
        nlp = spacy.load(model)
    except OSError:
        # If the model is not pre-installed, download and retry
        download(model)
        nlp = spacy.load(model)

    doc = nlp(text)

    return [(sent.start_char, sent.text) for sent in doc.sents]
