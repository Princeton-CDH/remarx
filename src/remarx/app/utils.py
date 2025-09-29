"""
Utility methods associated with the remarx app
"""

import contextlib
import pathlib
import tempfile
import webbrowser
from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager

import marimo as mo
import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

# Does this class have a public facing type definition?
from marimo._plugins.ui._impl.input import FileUploadResults

import remarx

# Server configuration
HOST = "localhost"
PORT = 8000


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager to open browser when server starts"""
    webbrowser.open(f"http://{HOST}:{PORT}/")
    yield


def launch_app() -> None:
    """Launch the remarx app in the default web browser"""
    # Create marimo asgi app
    server = mo.create_asgi_app()

    # Add notebooks
    server = server.with_app(
        path="/corpus-builder", root=remarx.app.corpus_builder.__file__
    )
    server = server.with_app(
        path="/quote-finder", root=remarx.app.quote_finder.__file__
    )

    # Create a FastAPI app with lifespan to open browser
    app = FastAPI(lifespan=lifespan)

    # Add redirect from root to corpus-builder
    @app.get("/")
    async def redirect_root() -> RedirectResponse:
        return RedirectResponse(url="/corpus-builder", status_code=302)

    app.mount("/", server.build())

    # Run server
    uvicorn.run(app, host=HOST, port=PORT)


def create_header() -> None:
    """Create the header for the remarx notebooks"""
    return mo.vstack(
        [
            mo.md("# `remarx`").center(),
            mo.md(f"Running version: {remarx.__version__}").center(),
            mo.md("---"),
            mo.nav_menu(
                {
                    "/corpus-builder": "### Sentence Corpus Builder",
                    "/quote-finder": "### Quote Finder",
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
