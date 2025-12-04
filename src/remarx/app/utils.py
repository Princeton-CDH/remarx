"""
Utility methods associated with the remarx app
"""

import contextlib
import logging
import pathlib
import tempfile
import webbrowser
from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Protocol, runtime_checkable

import marimo as mo
import polars as pl
import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

# Does this class have a public facing type definition?
from marimo._plugins.ui._impl.input import FileUploadResults

import remarx
from remarx.utils import CorpusPath, configure_logging, get_default_corpus_path

# Server configuration
HOST = "localhost"
PORT = 8000


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager to open browser when server starts"""
    webbrowser.open(f"http://{HOST}:{PORT}/")
    yield


async def redirect_root() -> RedirectResponse:
    """Redirect root path to corpus-builder, since app currently has no home page"""
    return RedirectResponse(url="/corpus-builder", status_code=302)


def launch_app() -> None:
    """Launch the remarx app in the default web browser"""
    # Configure logging once at startup to prevent multiple log files created by the notebooks
    log_file_path = configure_logging()

    # Log that the app is starting
    logger = logging.getLogger("remarx-app")
    logger.info("Remarx application starting")
    if log_file_path:
        logger.info(f"Logs are being written to: {log_file_path}")

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
    app.get("/")(redirect_root)

    app.mount("/", server.build())

    # Run server
    uvicorn.run(app, host=HOST, port=PORT)


def get_current_log_file() -> pathlib.Path | None:
    """
    Get the path to the current log file from the root logger's file handler.
    Returns None if logging is not configured to a file.
    """
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        if isinstance(handler, logging.FileHandler):
            return pathlib.Path(handler.baseFilename)
    return None


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


@runtime_checkable
class _HasPath(Protocol):
    """Protocol for objects that expose a filesystem path via a ``path`` attribute."""

    path: str | pathlib.Path | None


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


def summarize_corpus_selection(
    selection: _HasPath | str | pathlib.Path | None,
) -> dict[str, int | str] | None:
    """
    Summarize a sentence corpus CSV selected in the UI.

    Accepts either a file-browser selection (with a ``path`` attribute) or a
    filesystem path and returns corpus statistics that can be displayed in the
    Marimo table.
    """

    path_value = getattr(selection, "path", selection)
    if path_value is None:
        return None

    path = pathlib.Path(path_value)
    if not path.is_file():
        return None

    # Use lazy scanning so even large corpora only require lightweight
    # aggregations while collecting summary statistics.
    corpus = pl.scan_csv(path, infer_schema_length=0)
    total_sentences = corpus.select(pl.len()).collect().item()

    if "section_type" in corpus.collect_schema():
        counts = (
            corpus.group_by("section_type").agg(pl.len().alias("sentences")).collect()
        )
        body_sentences = int(
            counts.filter(pl.col("section_type") == "text")["sentences"].sum()
        )
        footnote_sentences = int(
            counts.filter(pl.col("section_type") == "footnote")["sentences"].sum()
        )
    else:
        body_sentences = total_sentences
        footnote_sentences = 0

    last_updated = datetime.fromtimestamp(path.stat().st_mtime).strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    return {
        "filename": path.name,
        "total sentences": int(total_sentences),
        "body text sentences": body_sentences,
        "footnote sentences": footnote_sentences,
        "last updated": last_updated,
    }


def handle_default_corpus_creation(
    button: mo.ui.run_button,
    default_dirs_initial: CorpusPath,
    *,
    ready_message: str = ":white_check_mark: Default corpus folders are ready.",
    missing_message: str = ":x: Default corpus folders were not found.",
) -> tuple[bool, CorpusPath, str, str]:
    """
    Update default corpus directory state based on the create button.

    :returns: Tuple of (ready flag, directories object, status message, callout kind)
    """

    default_dirs = default_dirs_initial
    default_dirs_ready_initial = default_dirs_initial.ready()
    default_dirs_ready = default_dirs_ready_initial

    status_msg = ready_message if default_dirs_ready_initial else missing_message
    callout_kind = "success" if default_dirs_ready_initial else "warn"

    if button.value and not default_dirs_ready_initial:
        default_dirs_ready, default_dirs = get_default_corpus_path(create=True)
        status_msg = f"Created default corpus folders under `{default_dirs.root}`"
        callout_kind = "success"

    return default_dirs_ready, default_dirs, status_msg, callout_kind
