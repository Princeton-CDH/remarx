"""
Utility functions for the remarx package
"""

import logging
import pathlib
import sys
from datetime import datetime
from typing import TextIO


def configure_logging(
    log_destination: pathlib.Path | TextIO | None = None,
    log_level: int = logging.INFO,
    stanza_log_level: int = logging.ERROR,
) -> pathlib.Path | None:
    """
    Configure logging for the remarx application.
    Supports logging to stdout, a specified file, or auto-generated timestamped file.

    :param log_destination: Where to write logs. Can be:
        - None (default): Creates a timestamped log file in ./logs/ directory
        - pathlib.Path: Write to the specified file path
        - sys.stdout: Write to console output
    :param log_level: Logging level for remarx logger (default to logging.INFO)
    :param stanza_log_level: Logging level for stanza logger (default to logging.ERROR)
    :return: Path to the created log file if file logging is used, None if stream logging
    """
    # Determine logging configuration based on log_destination parameter
    if log_destination is None:
        # Default: create timestamped log file
        log_dir = pathlib.Path.cwd() / "logs"
        log_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file_path = log_dir / f"remarx_{timestamp}.log"

        logging.basicConfig(
            filename=log_file_path,
            level=log_level,
            format="[%(asctime)s] %(levelname)s:%(name)s::%(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            encoding="utf-8",
        )
        created_log_file = log_file_path

    elif log_destination is sys.stdout:
        # Stream logging to stdout
        logging.basicConfig(
            stream=log_destination,
            level=log_level,
            format="[%(asctime)s] %(levelname)s:%(name)s::%(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        created_log_file = None

    else:
        # File logging to specified path
        log_file_path = log_destination
        log_file_path.parent.mkdir(parents=True, exist_ok=True)

        logging.basicConfig(
            filename=log_file_path,
            level=log_level,
            format="[%(asctime)s] %(levelname)s:%(name)s::%(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            encoding="utf-8",
        )
        created_log_file = log_file_path

    # Configure stanza logging level
    logging.getLogger("stanza").setLevel(stanza_log_level)

    return created_log_file
