from unittest.mock import Mock, patch

from remarx.app.utils import create_temp_input, launch_app


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
