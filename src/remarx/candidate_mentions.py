"""
This module contains functions for identifying (candidate) sentences that
might contain references to key titles or concepts.
"""

from typing import Generator

import stanza

NLP = stanza.Pipeline(lang="de", processors="tokenize,mwt,pos,lemma")


def lemmatize_sentence(sentence: stanza.Sentence, drop_punct: bool = True) -> str:
    """
    Converts a stanza sentence into its lemmatized form with each word
    separated by a space. By default, punctuation is removed.
    """
    return " ".join(
        [w.lemma for w in sentence.words if w.pos != "PUNCT" or not drop_punct]
    )


def lemmatize_text(text: str, drop_punct: bool = True) -> str:
    """
    Lemmatizes a text using `lemmatize_sentence` with sentences separated
    by a single space.
    """
    return " ".join(
        [lemmatize_sentence(s, drop_punct=drop_punct) for s in NLP(text).sentences]
    )


def find_sentences_with_phrase(
    search_phrases: list[str], text: str
) -> Generator[str, None, None]:
    """
    Returns a generator of sentences within a given text that contains oen of the
    given search phrases ignoring inflection.
    """
    # Lemmatize search phrase
    lemmatized_phrases = {lemmatize_text(phrase) for phrase in search_phrases}

    # Lemmatize & check if a sentence contains a search phrase
    for sentence in NLP(text).sentences:
        lemmatized_sent = lemmatize_sentence(sentence.str)
        if any(phrase in lemmatized_sent for phrase in lemmatized_phrases):
            yield sentence.str
