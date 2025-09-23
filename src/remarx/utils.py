"""
Utility functions for the remarx package
"""

import io
import logging
import pathlib
from datetime import datetime
from typing import TextIO


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
