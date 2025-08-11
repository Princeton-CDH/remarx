"""
Utility methods associated with the remarx app
"""

import contextlib

from marimo._cli import cli

from remarx import app


def launch_app() -> None:
    """Launch the remarx app into web browser."""
    with contextlib.suppress(SystemExit):
        # Prevent program from closing when marimo closes
        cli.main(["run", app.__file__])
