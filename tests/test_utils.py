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
    assert created_path.parent.name == "logs"

    # Check that the log file name starts with "remarx_" and ends with ".log"
    assert created_path.name.startswith("remarx_")
    assert created_path.suffix == ".log"
    assert created_path.exists()

    # Stanza logger level default
    assert logging.getLogger("stanza").getEffectiveLevel() == logging.ERROR

    # Write a line and ensure it's recorded
    logging.getLogger().info("Configuring logging with default file works")

    # Flush the log file (required by ruff check)
    for handler in logging.getLogger().handlers:
        with contextlib.suppress(Exception):
            handler.flush()

    assert "Configuring logging with default file works" in created_path.read_text(
        encoding="utf-8"
    )


def test_configure_logging_stdout_stream(capsys):
    created_path = configure_logging(sys.stdout, log_level=logging.INFO)

    assert created_path is None

    logging.getLogger().info("Configuring logging with stdout works")

    # Capture the output and check that it contains the log message
    captured = capsys.readouterr()

    assert "Configuring logging with stdout works" in captured.out


def test_configure_logging_specific_file(tmp_path):
    target = tmp_path / "nested" / "custom.log"
    created_path = configure_logging(target, log_level=logging.DEBUG)

    assert created_path == target
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
