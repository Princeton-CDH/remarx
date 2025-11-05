"""Utilities for rendering remarx logs inside marimo notebooks."""

from __future__ import annotations

import pathlib
from typing import Protocol, runtime_checkable

import marimo as mo


@runtime_checkable
class _ReadablePath(Protocol):
    """Protocol for any object that exposes a Path-like read_text method."""

    name: str

    def read_text(
        self,
        encoding: str | None = None,
        errors: str | None = None,
    ) -> str:  # pragma: no cover - Protocol
        """Return the file contents as text."""


def read_log_tail(
    file_path: _ReadablePath,
    max_lines: int = 10,
    *,
    encoding: str = "utf-8",
) -> str | None:
    """Return the last max_lines lines from file_path."""

    max_lines = max(0, max_lines)
    try:
        text = file_path.read_text(encoding=encoding, errors="replace")
    except FileNotFoundError:
        return None
    except TypeError:
        text = file_path.read_text()

    if not text:
        return ""

    lines = text.splitlines()
    if max_lines == 0:
        return ""
    return "\n".join(lines[-max_lines:])


def render_log_panel(
    log_file_path: pathlib.Path | None,
    *,
    refresh_control: mo.ui.refresh,
    refresh_ticks: int,
) -> mo.Html:
    """Render a reactive log viewer for the current marimo session."""

    hidden_refresh = refresh_control.style(display="none")
    _ = refresh_ticks

    display_text: str
    if log_file_path is not None:
        watched_log = mo.watch.file(log_file_path)
        log_tail = read_log_tail(watched_log)
        if log_tail is None:
            display_text = (
                f"Waiting for log file `{log_file_path.name}` to be created..."
            )
        else:
            display_text = log_tail or "[no log messages yet]"
    else:
        display_text = (
            "Logging is configured to stdout for this session; "
            "no log file is available to preview."
        )

    return mo.vstack(
        [
            hidden_refresh,
            mo.md(f"```text\n{display_text}\n```"),
        ],
    )


__all__ = [
    "read_log_tail",
    "render_log_panel",
]
