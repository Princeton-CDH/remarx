from remarx.app import corpus_builder, quote_finder
from remarx.app.utils import configure_logging


def test_corpus_builder_app():
    # Run the app - if it crashes, the test will fail
    corpus_builder.app.run()


def test_quote_finder_app():
    # Run the app - if it crashes, the test will fail
    quote_finder.app.run()


def test_corpus_builder_app_logging(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    configure_logging()
    corpus_builder.app.run()

    log_files = list((tmp_path / "logs").iterdir())
    log_text = log_files[-1].read_text()
    assert "Remarx Corpus Builder notebook started" in log_text


def test_quote_finder_app_logging(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    configure_logging()
    quote_finder.app.run()

    log_files = list((tmp_path / "logs").iterdir())
    log_text = log_files[-1].read_text()
    assert "Remarx Quote Finder notebook started" in log_text
