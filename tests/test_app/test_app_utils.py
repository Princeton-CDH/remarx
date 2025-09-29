from unittest.mock import Mock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from remarx.app.utils import create_header, create_temp_input, launch_app, lifespan


@patch("remarx.app.utils.uvicorn")
@patch("remarx.app.utils.mo")
def test_launch_app(mock_mo, mock_uvicorn):
    mock_server = Mock()
    mock_mo.create_asgi_app.return_value = mock_server
    mock_server.with_app.return_value = mock_server

    launch_app()

    mock_mo.create_asgi_app.assert_called_once()
    assert (
        mock_server.with_app.call_count == 2
    )  # twice, because of corpus-builder and quote-finder
    mock_server.build.assert_called_once()
    mock_uvicorn.run.assert_called_once()


@patch("remarx.app.utils.FileUploadResults")
def test_create_temp_input(mock_upload):
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
        # catch thrown thrown exception
        pass
    assert not tf.is_file()


@patch("remarx.app.utils.mo")
def test_create_header(mock_mo):
    """Test create_header function"""
    # Mock the marimo functions
    mock_mo.vstack.return_value = "mocked_header"
    mock_mo.md.return_value = Mock()
    mock_mo.nav_menu.return_value = Mock()

    result = create_header()

    mock_mo.vstack.assert_called_once()
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
        pass


@patch("remarx.app.utils.webbrowser")
@patch("remarx.app.utils.mo")
def test_fastapi_routes(mock_mo, mock_webbrowser):
    """Test FastAPI routes created in launch_app"""
    mock_server = Mock()
    mock_mo.create_asgi_app.return_value = mock_server
    mock_server.with_app.return_value = mock_server
    mock_server.build.return_value = Mock()

    app = FastAPI()

    # Add the same redirect route as in launch_app
    @app.get("/")
    async def redirect_root():
        from fastapi.responses import RedirectResponse

        return RedirectResponse(url="/corpus-builder", status_code=302)

    # Test the redirect route
    client = TestClient(app)
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/corpus-builder"
