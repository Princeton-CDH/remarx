"""
Utility functions for the remarx package
"""

import io
import logging
import pathlib
from dataclasses import dataclass
from datetime import datetime
from typing import TextIO

# Default data directory under the user's home directory
DEFAULT_DATA_ROOT = pathlib.Path.home() / "remarx-data"

# Default corpus directory locations within the data directory
DEFAULT_CORPUS_ROOT = DEFAULT_DATA_ROOT / "corpora"

# Default quote finder output directory
DEFAULT_QUOTE_OUTPUT_ROOT = DEFAULT_DATA_ROOT / "quotes"


@dataclass(slots=True)
class CorpusPath:
    """
    Paths for the default corpus directory structure.

    Populates unspecified directories based on the default data folder.
    Supports expansion of "~" or "~user" paths.
    """

    root: pathlib.Path | None = None
    original: pathlib.Path | None = None
    reuse: pathlib.Path | None = None

    def __post_init__(self) -> None:
        """
        Populate unset directories using the default data root, expanding "~"
        or "~user" values with `pathlib.Path.expanduser()` so shell-style root
        paths are accepted. Callers can override any directory; otherwise the
        root defaults to `DEFAULT_CORPUS_ROOT` under `remarx-data` and the
        `original` and `reuse` directories live as its subfolders.
        """
        base_root = (self.root or DEFAULT_CORPUS_ROOT).expanduser()
        self.root = base_root
        if self.original is None:
            self.original = base_root / "original"
        if self.reuse is None:
            self.reuse = base_root / "reuse"

    def ready(self) -> bool:
        """Return True if both default corpus directories already exist."""

        return all(path.exists() for path in (self.original, self.reuse))

    def ensure_directories(self) -> None:
        """Create the corpus directories if they do not exist."""

        for path in (self.root, self.original, self.reuse):
            path.mkdir(parents=True, exist_ok=True)


def get_default_corpus_path(
    create: bool = False,
) -> tuple[bool, CorpusPath]:
    """Return default corpus directories and optionally create them if missing."""

    directories = CorpusPath()

    if create:
        directories.ensure_directories()

    return directories.ready(), directories


def get_default_quote_output_path(
    create: bool = False,
) -> tuple[bool, pathlib.Path]:
    """
    Return the default quote finder output directory path and optionally create it if missing.

    :param create: If True, create the directory if it doesn't exist
    :returns: Tuple of (ready flag, path to quote output directory)
    """
    quote_output_path = DEFAULT_QUOTE_OUTPUT_ROOT.expanduser()
    ready = quote_output_path.exists()

    if create and not ready:
        quote_output_path.mkdir(parents=True, exist_ok=True)
        ready = True

    return ready, quote_output_path


def configure_logging(
    log_destination: pathlib.Path | TextIO | None = None,
    log_level: int = logging.INFO,
    stanza_log_level: int = logging.ERROR,
) -> pathlib.Path | None:
    """
    Configure logging for the remarx application.
    Supports logging to any text stream, a specified file, or auto-generated timestamped file.

    :param log_destination: Where to write logs. Can be:
        - None (default): Creates a timestamped log file in ./logs/ directory
        - pathlib.Path: Write to the specified file path
        - Any io.TextIOBase (e.g., sys.stdout, sys.stderr, or any io.TextIOBase): Write to the given stream
    :param log_level: Logging level for remarx logger (default to logging.INFO)
    :param stanza_log_level: Logging level for stanza logger (default to logging.ERROR)
    :return: Path to the created log file if file logging is used, None if stream logging
    """

    log_file_path: pathlib.Path | None = None
    config_output_opts: dict
    if log_destination is None:
        # Default: create timestamped log file under cwd / logs/
        log_dir = pathlib.Path.cwd() / "logs"
        log_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file_path = log_dir / f"remarx_{timestamp}.log"
        config_output_opts = {"filename": log_file_path, "encoding": "utf-8"}
    elif isinstance(log_destination, io.TextIOBase):
        # Only allow io.TextIOBase instances as streams (includes sys.stdout, sys.stderr)
        config_output_opts = {"stream": log_destination}
    else:
        # File logging to specified path
        log_file_path = log_destination
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        config_output_opts = {"filename": log_file_path, "encoding": "utf-8"}

    # Use the lowest of the requested levels so debug logs are captured when any
    # component (e.g., stanza) is set to DEBUG
    effective_level = min(log_level, stanza_log_level)

    logging.basicConfig(
        level=effective_level,
        format="[%(asctime)s] %(levelname)s:%(name)s::%(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,
        **config_output_opts,
    )

    # Configure stanza logging level
    logging.getLogger("stanza").setLevel(stanza_log_level)

    return log_file_path
