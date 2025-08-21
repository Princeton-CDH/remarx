"""
Utility methods associated with the remarx app
"""

import contextlib
import pathlib
import tempfile

from marimo._cli import cli

from remarx import app


def launch_app() -> None:
    """Launch the remarx app into web browser."""
    with contextlib.suppress(SystemExit):
        # Prevent program from closing when marimo closes
        cli.main(["run", app.__file__])


@contextlib.contextmanager
def create_temp_input(file_contents: bytes) -> pathlib.Path:
    """
    Create a temporary file containing the input file contents (as gathered by
    marimo.ui.file). This should be used in with statements.

    :returns: The path corresponding to the temporary file
    """
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False)  # noqa: SIM115
    try:
        temp_file.write(file_contents)
        yield pathlib.Path(temp_file.name)
    finally:
        temp_file.close()
