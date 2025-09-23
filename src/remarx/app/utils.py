"""
Utility methods associated with the remarx app
"""

import contextlib
import pathlib
import tempfile
from collections.abc import Generator

import marimo as mo
import uvicorn
from fastapi import FastAPI

# Does this class have a public facing type definition?
from marimo._plugins.ui._impl.input import FileUploadResults

import remarx


def launch_app() -> None:
    """Launch the remarx app in the default web browser"""
    # Create marimo asgi app
    server = mo.create_asgi_app()

    # Add notebooks
    ## For now set corpus builder as landing page
    server = server.with_app(path="", root=remarx.app.corpus_builder.__file__)
    server = server.with_app(
        path="/corpus-builder", root=remarx.app.corpus_builder.__file__
    )
    server = server.with_app(
        path="/quote-finder", root=remarx.app.quote_finder.__file__
    )

    # Create a FastAPI app
    app = FastAPI()
    app.mount("/", server.build())

    # Run server
    uvicorn.run(app, host="localhost", port=8000)


def create_header() -> None:
    """Create the header for the remarx notebooks"""
    return mo.vstack(
        [
            mo.md("# `remarx`").center(),
            mo.md(f"Running version: {remarx.__version__}").center(),
            mo.md("---"),
            mo.nav_menu(
                {
                    "/corpus-builder": "## Sentence Corpus Builder",
                    "/quote-finder": "## Quote Finder",
                }
            ).center(),
            mo.md("---"),
        ]
    )


@contextlib.contextmanager
def create_temp_input(
    file_upload: FileUploadResults,
) -> Generator[pathlib.Path, None, None]:
    """
    Context manager to create a temporary file with the file contents and name of a file uploaded
    to a web browser as returned by marimo.ui.file. This should be used in with statements.

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
