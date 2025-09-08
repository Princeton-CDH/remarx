"""
Utility methods associated with the remarx app
"""

import contextlib
import pathlib
import tempfile
from collections.abc import Generator

from marimo._cli import cli

# Does this class have a public facing type definition?
from marimo._plugins.ui._impl.input import FileUploadResults

from remarx import app


def launch_app() -> None:
    """Launch the remarx app into web browser."""
    with contextlib.suppress(SystemExit):
        # Prevent program from closing when marimo closes
        cli.main(["run", app.__file__])


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
