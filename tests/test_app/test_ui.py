from remarx.app.ui import app


def test_app():
    # Check application does not crash when run programmatically
    app.run()


def test_app_logging(tmp_path, monkeypatch):
    # Check default logging for app
    monkeypatch.chdir(tmp_path)
    app.run()

    log_files = list((tmp_path / "logs").iterdir())
    assert len(log_files) == 1
    log_text = log_files[0].read_text()
    # Has one log
    assert log_text.count("\n") == 1
    # Validate log
    assert log_text.endswith("INFO:remarx-app::Remarx UI notebook started\n")
