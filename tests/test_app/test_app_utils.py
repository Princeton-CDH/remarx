import logging
from unittest.mock import Mock, patch

import marimo
import pytest
from marimo._server.asgi import ASGIAppBuilder

# Types pulled from marimo source code
from starlette.types import ASGIApp

import remarx
from remarx.app.utils import (
    create_header,
    create_temp_input,
    get_current_log_file,
    launch_app,
    lifespan,
    redirect_root,
)


@patch("remarx.app.utils.uvicorn.run")
@patch("remarx.app.utils.mo")
@patch("remarx.app.utils.configure_logging")
def test_launch_app(mock_configure_logging, mock_mo, mock_uvicorn_run):
    """Test that launch_app sets up the application structure correctly"""
    mock_server = Mock(spec=ASGIAppBuilder)
    mock_mo.create_asgi_app.return_value = mock_server
    mock_server.with_app.return_value = mock_server
    mock_server.build.return_value = Mock(spec=ASGIApp)

    # Mock configure_logging to return a log file path
    mock_configure_logging.return_value = "/path/to/log/file.log"

    launch_app()

    # Verify logging is configured first
    mock_configure_logging.assert_called_once()

    # Verify marimo app creation and configuration
    mock_mo.create_asgi_app.assert_called_once()
    assert mock_server.with_app.call_count == 2  # corpus-builder and quote-finder
    mock_server.build.assert_called_once()

    # Verify server startup
    mock_uvicorn_run.assert_called_once()


@patch("remarx.app.utils.FileUploadResults")
def test_create_temp_input(mock_upload):
    """Test temporary file creation and cleanup"""
    # Create mock file upload
    mock_upload.name = "file.txt"
    mock_upload.contents = b"bytes"

    # Normal case
    with create_temp_input(mock_upload) as tf:
        assert tf.is_file()
        assert tf.suffix == ".txt"
        assert tf.read_text() == "bytes"
    assert not tf.is_file()

    # Check temp file is closed if an exception is raised
    try:
        with create_temp_input(mock_upload) as tf:
            raise ValueError
    except ValueError:
        # catch thrown exception
        pass
    assert not tf.is_file()


@patch("remarx.app.utils.mo.vstack")
@patch("remarx.app.utils.mo.nav_menu")
@patch("remarx.app.utils.mo.md")
def test_create_header(mock_md, mock_nav_menu, mock_vstack):
    """Test create_header function"""
    # Mock the marimo functions
    ## Work around for HTML centering
    mock_md.side_effect = (
        lambda x: x
        if x == "---"
        else Mock(spec=marimo.Html, **{"text": x, "center.return_value": x})
    )
    mock_nav_menu.return_value = Mock(
        spec=marimo.Html, **{"center.return_value": "nav_bar"}
    )
    mock_vstack.return_value = "mocked_header"

    result = create_header()
    mock_nav_menu.assert_called_once()
    assert mock_md.call_count == 4
    mock_vstack.assert_called_once_with(
        [
            "# `remarx`",
            f"Running version: {remarx.__version__}",
            "---",
            "nav_bar",
            "---",
        ]
    )
    assert result == "mocked_header"


@patch("remarx.app.utils.webbrowser")
@pytest.mark.asyncio
async def test_lifespan(mock_webbrowser):
    """Test lifespan context manager"""
    from fastapi import FastAPI

    # Create a mock app
    app = FastAPI()

    # Test the lifespan context manager
    async with lifespan(app):
        mock_webbrowser.open.assert_called_once_with("http://localhost:8000/")


@pytest.mark.asyncio
async def test_redirect_root():
    """Test redirect_root function directly"""
    response = await redirect_root()

    assert response.status_code == 302
    assert response.headers["location"] == "/corpus-builder"


def test_get_current_log_file(tmp_path):
    logger = logging.getLogger()
    original_handlers = logger.handlers[:]

    # remove all handlers
    for handler in original_handlers:
        logger.removeHandler(handler)

    # should return None when there is no FileHandler
    stream_handler = logging.StreamHandler()
    logger.addHandler(stream_handler)
    try:
        result = get_current_log_file()
        assert result is None
    finally:
        logger.removeHandler(stream_handler)

    # should return log_file path when there is a FileHandler
    log_file = tmp_path / "test.log"
    file_handler = logging.FileHandler(log_file)
    logger.addHandler(file_handler)
    try:
        result = get_current_log_file()
        assert result == log_file
    finally:
        logger.removeHandler(file_handler)
        file_handler.close()

    # restore original handlers
    for handler in original_handlers:
        logger.addHandler(handler)


def test_launch_app_logging(tmp_path, monkeypatch):
    """Test that launch_app logs the correct startup messages"""
    monkeypatch.chdir(tmp_path)

    with patch("remarx.app.utils.uvicorn.run"):
        launch_app()

    log_files = list((tmp_path / "logs").iterdir())
    log_text = log_files[-1].read_text()
    assert "Remarx application starting" in log_text
    assert "Logs are being written to:" in log_text
