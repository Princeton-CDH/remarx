from remarx.app import corpus_builder, quote_finder


def test_corpus_builder_app():
    # Run the app - if it crashes, the test will fail
    corpus_builder.app.run()


def test_corpus_builder_app_logging(tmp_path, monkeypatch):
    # Check default logging for corpus_builder app
    monkeypatch.chdir(tmp_path)
    corpus_builder.app.run()

    log_files = list((tmp_path / "logs").iterdir())
    assert len(log_files) == 1
    log_text = log_files[0].read_text()
    # Has one log
    assert log_text.count("\n") == 1
    # Validate log
    assert log_text.endswith(
        "INFO:remarx-app::Remarx Corpus Builder notebook started\n"
    )


def test_quote_finder_app():
    # Run the app - if it crashes, the test will fail
    quote_finder.app.run()


def test_quote_finder_app_logging(tmp_path, monkeypatch):
    # Check default logging for quote_finder app
    monkeypatch.chdir(tmp_path)
    quote_finder.app.run()

    log_files = list((tmp_path / "logs").iterdir())
    assert len(log_files) == 1
    log_text = log_files[0].read_text()
    # Has one log
    assert log_text.count("\n") == 1
    # Validate log
    assert log_text.endswith("INFO:remarx-app::Remarx Quote Finder notebook started\n")
