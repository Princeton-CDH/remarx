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
    """
    Return the last max_lines from file_path.
    None is returned when the underlying file does not yet exist.
    """

    max_lines = max(0, max_lines)
    try:
        text = file_path.read_text(encoding=encoding, errors="replace")
    except FileNotFoundError:
        return None
    except TypeError:
        # marimo's FileState.read_text does not accept encoding/errors
        text = file_path.read_text()

    if not text:
        return ""

    lines = text.splitlines()
    if max_lines == 0:
        return ""
    tail = lines[-max_lines:]
    return "\n".join(tail)


def create_log_refresh_control(
    *,
    key: str = "default",
) -> mo.ui.refresh:
    """Create or reuse the refresh control used to trigger log polling."""

    return mo.ui.refresh(
        options=["1s"],
        default_interval="1s",
    )


def render_log_panel(
    log_file_path: pathlib.Path | None,
    *,
    panel_title: str = "Live remarx logs",
    refresh_control: mo.ui.refresh | None = None,
    refresh_ticks: int | None = None,
) -> mo.Html:
    """Render a reactive log viewer for the current marimo session."""

    refresh_ui = (
        refresh_control
        if refresh_control is not None
        else create_log_refresh_control(key="default")
    )
    hidden_refresh_ui = refresh_ui.style(display="none")

    if refresh_ticks is not None:
        _ = refresh_ticks
    elif refresh_control is not None:
        try:
            _ = refresh_control.value
        except RuntimeError:
            _ = None
    else:
        _ = None

    if log_file_path is None:
        return mo.vstack(
            [
                hidden_refresh_ui,
                mo.callout(
                    mo.md(
                        "Logging is configured to stdout for this session; "
                        "no log file is available to preview."
                    ),
                    kind="info",
                ),
            ],
            align="stretch",
            gap="0.5em",
        )

    watched_log = mo.watch.file(log_file_path)
    log_tail = read_log_tail(watched_log)
    if log_tail is None:
        return mo.vstack(
            [
                hidden_refresh_ui,
                mo.callout(
                    mo.md(
                        f"Waiting for log file `{log_file_path.name}` to be created..."
                    ),
                    kind="info",
                ),
            ],
            align="stretch",
            gap="0.5em",
        )

    display_text = log_tail or "[no log messages yet]"
    log_panel = mo.md(f"```text\n{display_text}\n```")

    return mo.vstack(
        [
            hidden_refresh_ui,
            log_panel,
        ],
        align="stretch",
        gap="0.5em",
    )


__all__ = [
    "create_log_refresh_control",
    "read_log_tail",
    "render_log_panel",
]
