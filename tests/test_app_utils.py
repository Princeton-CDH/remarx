import pathlib
from unittest.mock import MagicMock, patch

import remarx.app
from remarx.app_utils import create_temp_input, launch_app


@patch("remarx.app_utils.cli")
def test_launch_app(mock_cli):
    launch_app()
    mock_cli.main.assert_called_once_with(["run", remarx.app.__file__])


@patch("remarx.app_utils.tempfile.NamedTemporaryFile")
def test_create_temp_input(mock_temp_file):
    working_tf = MagicMock()
    working_tf.name = "foo"
    mock_temp_file.return_value = working_tf

    with create_temp_input("bytes") as tf:
        mock_temp_file.assert_called_once_with(delete=False)
        working_tf.write.assert_called_once_with("bytes")
        assert tf == pathlib.Path("foo")
    working_tf.close.assert_called_once_with()
