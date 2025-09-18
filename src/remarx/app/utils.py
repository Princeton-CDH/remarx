"""
Utility methods associated with the remarx app
"""

import contextlib
import logging
import os
import pathlib
import tempfile
from collections.abc import Generator
from datetime import datetime

from marimo._cli import cli

# Does this class have a public facing type definition?
from marimo._plugins.ui._impl.input import FileUploadResults

from remarx.app import ui


def setup_logging() -> pathlib.Path:
    """
    Configure file logging at INFO level to capture
    application events for debugging and user support.

    :return: Path to the created log file
    """
    # Create logs directory
    log_dir = pathlib.Path.cwd() / "logs"
    log_dir.mkdir(exist_ok=True)

    # Create timestamped log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"remarx_{timestamp}.log"

    # Configure basic file logging
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        encoding="utf-8",
    )

    # Suppress stanza's verbose logging to only show errors
    logging.getLogger("stanza").setLevel(logging.ERROR)

    return log_file


def launch_app() -> None:
    """Launch the remarx app into web browser."""
    # Set up logging and store path for UI access
    log_file = setup_logging()
    os.environ["REMARX_LOG_FILE"] = str(log_file)

    with contextlib.suppress(SystemExit):
        # Prevent program from closing when marimo closes
        cli.main(["run", ui.__file__])


@contextlib.contextmanager
def create_temp_input(
    file_upload: FileUploadResults,
) -> Generator[pathlib.Path, None, None]:
    """
    Context manager to create a temporary file with the file contents and name of a file uploaded
    to a web browser as returned by  marimo.ui.file. This should be used in with statements.

    :returns: Yields the path to the temporary file
    """
    temp_file = tempfile.NamedTemporaryFile(  # noqa: SIM115
        delete=False,
        suffix=pathlib.Path(file_upload.name).suffix,
    )
    try:
        temp_file.write(file_upload.contents)
        # Close to ensure write occurs
        temp_file.close()
        yield pathlib.Path(temp_file.name)
    finally:
        if not temp_file.closed:
            temp_file.close()
        pathlib.Path.unlink(temp_file.name)
