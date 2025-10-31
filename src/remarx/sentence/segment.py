"""
Provides functionality to break down input text into individual
sentences and return them as tuples containing the character index where each
sentence begins and the sentence text itself.
"""

import spacy
from flair.splitter import SpacySentenceSplitter
from flair.tokenization import SpacyTokenizer


def _get_flair_spacy_de_splitter() -> SpacySentenceSplitter:
    """
    Cached Flair Spacy-backed German sentence splitter.

    Uses the "de_core_news_sm" spaCy model for German sentence segmentation.
    """
    splitter = getattr(_get_flair_spacy_de_splitter, "_cached_splitter", None)
    if splitter is None:
        nlp = spacy.load("de_core_news_sm")
        tokenizer = SpacyTokenizer("de_core_news_sm")
        splitter = SpacySentenceSplitter(nlp, tokenizer=tokenizer)
        _get_flair_spacy_de_splitter._cached_splitter = splitter
    return splitter


_SEGMENTER_BACKEND = None


def set_segmenter_backend(backend: str) -> None:
    """
    Set the active segmenter backend.

    Allowed: 'stanza', 'stanza_optimized', 'flair_spacy_de'
    """
    global _SEGMENTER_BACKEND
    _SEGMENTER_BACKEND = backend


def segment_text(text: str, language: str = "de") -> list[tuple[int, str]]:
    """
    Segment text into sentences with start indices.

    Supports three backends for profiling:
    - 'stanza': Baseline Stanza (no caching) - **default**
    - 'stanza_optimized': Optimized Stanza with pipeline caching
    - 'flair_spacy_de': Flair with spaCy backend for German
    """
    # Ensure text is a plain string (handles lxml._ElementUnicodeResult and similar)
    text = str(text)

    backend = _SEGMENTER_BACKEND or "stanza"  # default fallback to stanza

    if backend == "stanza":
        # Baseline: construct a new pipeline each call (no reuse)
        import stanza  # type: ignore
        from stanza import DownloadMethod  # type: ignore

        segmenter = stanza.Pipeline(
            lang=language,
            processors="tokenize",
            download_method=DownloadMethod.REUSE_RESOURCES,
        )
        processed_doc = segmenter(text)
        sentences = [(s.tokens[0].start_char, s.text) for s in processed_doc.sentences]
        return sentences

    if backend == "stanza_optimized":
        # Cached Stanza pipeline
        import stanza  # type: ignore
        from stanza import DownloadMethod  # type: ignore

        # cache by language
        cache = getattr(segment_text, "_stanza_cache", {})
        segmenter = cache.get(language)
        if segmenter is None:
            segmenter = stanza.Pipeline(
                lang=language,
                processors="tokenize",
                download_method=DownloadMethod.REUSE_RESOURCES,
            )
            cache[language] = segmenter
            segment_text._stanza_cache = cache
        processed_doc = segmenter(text)
        sentences = [(s.tokens[0].start_char, s.text) for s in processed_doc.sentences]
        return sentences

    # Default: flair_spacy_de
    splitter = _get_flair_spacy_de_splitter()
    flair_sentences = splitter.split(text)

    results: list[tuple[int, str]] = []
    search_from = 0
    for sent in flair_sentences:
        sent_text = sent.to_plain_string()
        if not sent_text:
            continue
        start_idx = text.find(sent_text, search_from)
        if start_idx == -1:
            start_idx = 0
        results.append((start_idx, sent_text))
        search_from = start_idx + len(sent_text)

    return results
