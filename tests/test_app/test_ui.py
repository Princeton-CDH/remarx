from remarx.app import corpus_builder, quote_finder


def test_corpus_builder_app():
    # Test by running the notebook app - if it crashes, the test will fail
    corpus_builder.app.run()


def test_quote_finder_app():
    # Test by running the notebook app - if it crashes, the test will fail
    quote_finder.app.run()
