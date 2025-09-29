import marimo

from remarx.app import corpus_builder, quote_finder


def test_corpus_builder_app():
    assert hasattr(corpus_builder, "app")
    assert isinstance(corpus_builder.app, marimo.App)


def test_quote_finder_app():
    assert hasattr(quote_finder, "app")
    assert isinstance(quote_finder.app, marimo.App)
