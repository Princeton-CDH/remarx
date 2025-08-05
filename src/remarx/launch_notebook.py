"""
A script for launching a remarx marimo notebook. It takes the name of the
name of the notebook to be launched.

Example: launch_notebook.py remarx_gui
"""

import argparse
import importlib.resources
import subprocess
import sys
from typing import Never


def launch_notebook(notebook: str) -> Never:
    """
    Launches a specified remarx notebook.
    """

    # Get path to notebook
    notebook_path = importlib.resources.files("remarx.notebooks").joinpath(
        f"{notebook}.py"
    )

    if not notebook_path.is_file():
        err_msg = f"ERROR: {notebook} notebook not found"
        print(err_msg, file=sys.stderr)
        sys.exit(1)

    # Launch notebook
    try:
        subprocess.run(["marimo", "run", notebook_path])
    except KeyboardInterrupt:
        # Exit application
        sys.exit(0)


def main() -> Never:
    """
    Command-line access for launching a specified remarx notebook
    """

    parser = argparse.ArgumentParser(
        description="Launch a remarx notebook",
    )
    parser.add_argument(
        "notebook",
        help="Name of notebook to be launched",
    )

    args = parser.parse_args()
    launch_notebook(args.notebook)


if __name__ == "__main__":
    main()
