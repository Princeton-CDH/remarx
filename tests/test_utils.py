import contextlib
import logging
import sys
from pathlib import Path

import pytest

from remarx.utils import configure_logging


@pytest.fixture(autouse=True)
def reset_logging():
    """Ensure a clean logging configuration for each test."""
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        with contextlib.suppress(Exception):
            handler.close()


def test_configure_logging_default_creates_timestamped_file(tmp_path, monkeypatch):
    """Test that the default configuration creates a timestamped log file."""
    # Run in a temporary CWD so logs land under tmp_path/logs/
    monkeypatch.chdir(tmp_path)
    created_path = configure_logging()

    assert isinstance(created_path, Path)
    logs_dir = created_path.parent
    assert logs_dir.name == "logs"
    assert logs_dir.is_dir()

    # Check that the log file name starts with "remarx_" and ends with ".log"
    assert created_path.name.startswith("remarx_")
    assert created_path.suffix == ".log"
    assert created_path.exists()

    # Check root logger level is the expected default (INFO)
    root_logger = logging.getLogger()
    assert root_logger.getEffectiveLevel() == logging.INFO

    # Inspect the configured logging handler: should be a FileHandler pointing to created_path
    file_handlers = [
        h for h in root_logger.handlers if isinstance(h, logging.FileHandler)
    ]
    assert any(Path(h.baseFilename) == created_path for h in file_handlers)

    # Stanza logger level default
    assert logging.getLogger("stanza").getEffectiveLevel() == logging.ERROR


def test_configure_logging_stdout_stream(tmp_path, monkeypatch, capsys):
    # Run in a temporary CWD and ensure no logs/ directory is created when streaming to stdout
    monkeypatch.chdir(tmp_path)
    created_path = configure_logging(sys.stdout, log_level=logging.INFO)

    assert created_path is None

    logging.getLogger().info("Configuring logging with stdout works")

    # Capture the output and check that it contains the log message
    captured = capsys.readouterr()
    assert "Configuring logging with stdout works" in captured.out
    # Confirm that no log directory or file was created as we logged to stdout
    assert not (tmp_path / "logs").exists()


def test_configure_logging_specific_file(tmp_path):
    target = tmp_path / "nested" / "custom.log"
    created_path = configure_logging(target, log_level=logging.DEBUG)

    assert created_path == target
    # The file itself should exist, not just the parent directory
    assert target.exists()

    logging.getLogger().debug("Configuring logging with specific file works")

    for handler in logging.getLogger().handlers:
        with contextlib.suppress(Exception):
            handler.flush()

    assert "Configuring logging with specific file works" in target.read_text(
        encoding="utf-8"
    )


def test_configure_logging_with_stanza_log_level():
    created_path = configure_logging(stanza_log_level=logging.DEBUG)
    assert logging.getLogger("stanza").getEffectiveLevel() == logging.DEBUG
    logging.getLogger().debug("Configuring logging with stanza log level works")

    for handler in logging.getLogger().handlers:
        with contextlib.suppress(Exception):
            handler.flush()

    assert "Configuring logging with stanza log level works" in created_path.read_text(
        encoding="utf-8"
    )
