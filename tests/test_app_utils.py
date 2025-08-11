from unittest.mock import patch

import remarx.app
from remarx.app_utils import launch_app


@patch("remarx.app_utils.cli")
def test_launch_app(mock_cli):
    launch_app()
    mock_cli.main.assert_called_once_with(["run", remarx.app.__file__])
