import contextlib
import io
import logging
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from remarx.utils import (
    CorpusPath,
    configure_logging,
    get_default_corpus_path,
    get_default_quote_output_path,
)


@pytest.fixture(autouse=True)
def reset_logging():
    """
    This fixture forcibly removes all handlers from the root logger before each test,
    guaranteeing that logging.basicConfig in the code under test will always add a fresh handler.
    """
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        with contextlib.suppress(Exception):
            handler.close()


def test_configure_logging_default_creates_timestamped_filename(tmp_path, monkeypatch):
    """Test that the default configuration creates a timestamped log filename and directory."""
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

    # Check root logger level is the expected default (INFO)
    root_logger = logging.getLogger()
    assert root_logger.getEffectiveLevel() == logging.INFO

    # there should be only one handler with our fixture, which should be a FileHandler
    handler = root_logger.handlers[-1]
    assert isinstance(handler, logging.FileHandler)
    assert Path(handler.baseFilename) == created_path

    # Stanza logger level default
    assert logging.getLogger("stanza").getEffectiveLevel() == logging.ERROR


# use parametrize to test with different streams
@pytest.mark.parametrize("stream", [sys.stdout, sys.stderr, io.StringIO()])
def test_configure_logging_stream(tmp_path, monkeypatch, stream):
    # Run in a temporary CWD and ensure no logs/ directory is created when streaming to a text stream
    monkeypatch.chdir(tmp_path)
    created_path = configure_logging(log_destination=stream, log_level=logging.INFO)

    assert created_path is None

    root_logger = logging.getLogger()
    handler = root_logger.handlers[-1]
    assert isinstance(handler, logging.StreamHandler)
    assert getattr(handler, "stream", None) is stream

    # Confirm that no log directory or file was created as we logged to a stream
    assert not (tmp_path / "logs").exists()


def test_configure_logging_specific_file(tmp_path):
    target_path = tmp_path / "nested" / "custom.log"
    created_path = configure_logging(target_path, log_level=logging.DEBUG)

    assert created_path == target_path
    # Only require that the parent directory exists; file may be created on first write
    assert target_path.parent.exists()

    root_logger = logging.getLogger()
    handler = root_logger.handlers[-1]
    assert isinstance(handler, logging.FileHandler)
    assert Path(handler.baseFilename) == target_path
    # The handler should be set to the correct log level (DEBUG or NOTSET if inherited)
    assert handler.level in (logging.NOTSET, logging.DEBUG)


def test_configure_logging_with_stanza_log_level(tmp_path, monkeypatch):
    # Use a clean temp directory for logs
    monkeypatch.chdir(tmp_path)
    configure_logging(stanza_log_level=logging.DEBUG)

    # Check that the stanza logger is set to DEBUG
    stanza_logger = logging.getLogger("stanza")
    assert stanza_logger.getEffectiveLevel() == logging.DEBUG


@pytest.fixture
def patched_default_corpus_paths(tmp_path):
    data_root = tmp_path / "remarx-data"
    corpora_root = data_root / "corpora"
    with (
        patch("remarx.utils.DEFAULT_DATA_ROOT", data_root),
        patch("remarx.utils.DEFAULT_CORPUS_ROOT", corpora_root),
    ):
        yield corpora_root


def test_get_default_corpus_path_reports_missing(patched_default_corpus_paths):
    ready, dirs = get_default_corpus_path()
    root = patched_default_corpus_paths

    assert not ready
    assert dirs.root == root
    assert dirs.original == root / "original"
    assert dirs.reuse == root / "reuse"
    assert not dirs.original.exists()
    assert not dirs.reuse.exists()


def test_get_default_corpus_path_creates(patched_default_corpus_paths):
    ready, dirs = get_default_corpus_path(create=True)

    assert ready
    assert dirs.original.exists()
    assert dirs.reuse.exists()

    ready_again, _ = get_default_corpus_path()
    assert ready_again


def test_corpus_path_post_init_sets_defaults(patched_default_corpus_paths):
    """Test that __post_init__ sets original and reuse when they are None."""
    root = patched_default_corpus_paths
    dirs = CorpusPath()

    assert dirs.original == root / "original"
    assert dirs.reuse == root / "reuse"
    assert dirs.root == root


def test_corpus_path_ready_and_ensure_directories(patched_default_corpus_paths):
    root = patched_default_corpus_paths
    dirs = CorpusPath()

    assert dirs.root == root
    assert not dirs.ready()

    assert not dirs.root.exists()
    assert not dirs.original.exists()
    assert not dirs.reuse.exists()

    dirs.ensure_directories()

    assert dirs.ready()
    assert dirs.root.exists()
    assert dirs.original.exists()
    assert dirs.reuse.exists()


def test_get_default_quote_output_path_creates(tmp_path):
    data_root = tmp_path / "remarx-data"
    quote_output_root = data_root / "quote-finder-output"
    with (
        patch("remarx.utils.DEFAULT_DATA_ROOT", data_root),
        patch("remarx.utils.DEFAULT_QUOTE_OUTPUT_ROOT", quote_output_root),
    ):
        ready, path = get_default_quote_output_path(create=True)
        assert ready
        assert path.exists()
