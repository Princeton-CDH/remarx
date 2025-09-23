from unittest.mock import patch

from remarx.app import ui
from remarx.app.utils import create_temp_input, launch_app


@patch("remarx.app.utils.cli")
def test_launch_app(mock_cli):
    launch_app()
    mock_cli.main.assert_called_once_with(["run", ui.__file__])


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
