"""
A script for launching the remarx GUI application.
"""

from typing import Never

from remarx.launch_notebook import launch_notebook


def main() -> Never:
    """
    Launches the remarx GUI application (i.e. remarx_gui notebook)
    """
    launch_notebook("remarx_gui")


if __name__ == "__main__":
    main()
