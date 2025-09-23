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
    assert logs_dir == tmp_path / "logs"
    assert logs_dir.is_dir()

    # Check that the log file name starts with "remarx_" and ends with ".log"
    assert created_path.name.startswith("remarx_")
    assert created_path.suffix == ".log"
    assert created_path.exists()

    # Check root logger level is the expected default (INFO)
    root_logger = logging.getLogger()
    assert root_logger.getEffectiveLevel() == logging.INFO

    # With the reset_logging fixture, there should be only one handler
    assert len(root_logger.handlers) == 1
    handler = root_logger.handlers[0]
    assert isinstance(handler, logging.FileHandler)
    assert Path(handler.baseFilename) == created_path

    # Stanza logger level default
    assert logging.getLogger("stanza").getEffectiveLevel() == logging.ERROR


def test_configure_logging_stdout_stream(tmp_path, monkeypatch):
    # Run in a temporary CWD and ensure no logs/ directory is created when streaming to stdout
    monkeypatch.chdir(tmp_path)
    created_path = configure_logging(sys.stdout, log_level=logging.INFO)

    assert created_path is None

    # there should be only one handler, which should be a StreamHandler to sys.stdout
    root_logger = logging.getLogger()
    assert len(root_logger.handlers) == 1
    handler = root_logger.handlers[0]
    assert isinstance(handler, logging.StreamHandler)
    assert getattr(handler, "stream", None) is sys.stdout

    # Confirm that no log directory or file was created as we logged to stdout
    assert not (tmp_path / "logs").exists()


def test_configure_logging_specific_file(tmp_path):
    target_path = tmp_path / "nested" / "custom.log"
    created_path = configure_logging(target_path, log_level=logging.DEBUG)

    assert created_path == target_path
    assert target_path.exists()

    # expect only one handler and it should be a FileHandler
    root_logger = logging.getLogger()
    assert len(root_logger.handlers) == 1
    handler = root_logger.handlers[0]
    assert isinstance(handler, logging.FileHandler)
    assert Path(handler.baseFilename) == target_path
    # The handler should be set to the correct log level (DEBUG or NOTSET if inherited)
    assert handler.level in (logging.NOTSET, logging.DEBUG)


def test_configure_logging_with_stanza_log_level(tmp_path, monkeypatch):
    # Use a clean temp directory for logs
    monkeypatch.chdir(tmp_path)
    created_path = configure_logging(stanza_log_level=logging.DEBUG)

    # Check that the stanza logger is set to DEBUG
    stanza_logger = logging.getLogger("stanza")
    assert stanza_logger.getEffectiveLevel() == logging.DEBUG

    # Check that a FileHandler is present and points to the created_path
    root_logger = logging.getLogger()
    assert any(
        isinstance(h, logging.FileHandler) and Path(h.baseFilename) == created_path
        for h in root_logger.handlers
    )
