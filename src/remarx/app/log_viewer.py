"""Utilities for rendering remarx logs inside marimo notebooks."""

from __future__ import annotations

import html
import pathlib
from collections.abc import Sequence
from typing import Protocol, runtime_checkable

import marimo as mo

DEFAULT_LOG_LINES = 10
REFRESH_OPTIONS = ["1s", "5s", "10s", "30s"]
DEFAULT_REFRESH_INTERVAL = "1s"


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
    max_lines: int = DEFAULT_LOG_LINES,
    *,
    encoding: str = "utf-8",
) -> str | None:
    """
    Return the last ``max_lines`` from ``file_path``.

    ``None`` is returned when the underlying file does not yet exist.
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
    options: Sequence[str] = REFRESH_OPTIONS,
    default_interval: str = DEFAULT_REFRESH_INTERVAL,
) -> mo.ui.refresh:
    """Create or reuse the refresh control used to trigger log polling."""

    return mo.ui.refresh(
        options=list(options),
        default_interval=default_interval,
    )


def render_log_panel(
    log_file_path: pathlib.Path | None,
    max_lines: int = DEFAULT_LOG_LINES,
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

    guidance_md = None

    if log_file_path is None:
        return mo.vstack(
            [
                guidance_md,
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
    log_tail = read_log_tail(watched_log, max_lines=max_lines)
    if log_tail is None:
        return mo.vstack(
            [
                guidance_md,
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
    escaped_text = html.escape(display_text)
    log_panel = mo.Html(
        '<div style="background-color:#111827;border:1px solid #1d4ed8;'
        'border-radius:10px;padding:0.85em;box-shadow:0 2px 6px rgba(0,0,0,0.25);">'
        '<pre style="margin:0;font-family:var(--marimo-font-mono,monospace);'
        "font-size:0.9rem;line-height:1.4;color:#f8fafc;white-space:pre-wrap;"
        'overflow:auto;tab-size:4;max-height:24rem;">'
        f"{escaped_text}"
        "</pre></div>"
    )

    return mo.vstack(
        [
            guidance_md,
            hidden_refresh_ui,
            log_panel,
        ],
        align="stretch",
        gap="0.5em",
    )


__all__ = [
    "DEFAULT_LOG_LINES",
    "create_log_refresh_control",
    "read_log_tail",
    "render_log_panel",
]
