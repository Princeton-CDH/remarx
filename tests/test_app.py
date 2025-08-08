from unittest.mock import patch

import remarx
from remarx.app import app


@patch("remarx.app.marimo.running_in_notebook", return_value=True)
def test_app_as_nb(mock_run_check):
    # Simulate running as notebook
    app.run()
    mock_run_check.assert_called_once()


@patch("remarx.app.marimo.running_in_notebook", return_value=False)
@patch("remarx.app.marimo._cli.cli")
def test_app_as_script(mock_cli, mock_run_check):
    # Simulate running as script
    app.run()
    mock_run_check.assert_called_once()
    mock_cli.main.assert_called_once_with(["run", remarx.app.__file__])
