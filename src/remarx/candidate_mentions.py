"""
This module contains functions for identifying (candidate) sentences that
might contain references to key titles or concepts.
"""

from typing import Generator

import stanza

NLP = stanza.Pipeline(lang="de", processors="tokenize,mwt,pos,lemma")


def get_lemmatized_form(text: str, drop_punct: bool = True) -> str:
    """
    Converts a text into its lemmatized form. By default, punctuation is removed.
    """
    lemmas = []
    for sentence in NLP(text).sentences:
        for word in sentence.words:
            if word.pos != "PUNCT" or not drop_punct:
                lemmas.append(word.lemma)
    return " ".join(lemmas)


def get_sentences_with_key(key: str, text: str) -> Generator[str, None, None]:
    """
    Returns a generator of sentences within a given text that contain the
    given search ignoring inflection.
    """
    # Lemmatize key
    key_lemmas = get_lemmatized_form(key)

    # Lemmatize & check each sentence
    for sentence in NLP(text).sentences:
        sent_lemmas = get_lemmatized_form(sentence.str)
        if key_lemmas in sent_lemmas:
            yield sentence.str
