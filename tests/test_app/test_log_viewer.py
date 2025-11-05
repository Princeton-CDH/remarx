import pathlib

import pytest

from remarx.app.log_viewer import (
    create_log_refresh_control,
    read_log_tail,
    render_log_panel,
)


class DummyPath:
    def __init__(self, text: str, name: str = "dummy.log") -> None:
        self._text = text
        self.name = name

    def read_text(self, *_, **__) -> str:
        return self._text


class TypeErrorPath:
    def __init__(self, text: str) -> None:
        self._text = text
        self.name = "type-error.log"

    def read_text(self, *args, **kwargs):
        if args or kwargs:
            raise TypeError("unexpected kwargs")
        return self._text


def test_read_log_tail_handles_missing_file(tmp_path: pathlib.Path) -> None:
    missing_file = tmp_path / "missing.log"
    assert read_log_tail(missing_file) is None


@pytest.mark.parametrize(
    "contents, max_lines, expected",
    [
        ("", 10, ""),
        ("a\nb\nc", 2, "b\nc"),
        ("line", 5, "line"),
        ("line1\nline2\n", 1, "line2"),
        ("line1\nline2", 0, ""),
    ],
)
def test_read_log_tail_returns_expected_lines(
    contents: str, max_lines: int, expected: str
) -> None:
    path = DummyPath(contents)
    assert read_log_tail(path, max_lines=max_lines) == expected


def test_read_log_tail_falls_back_when_encoding_not_supported() -> None:
    path = TypeErrorPath("first\nsecond")
    assert read_log_tail(path, max_lines=1) == "second"


def test_create_log_refresh_control_returns_refresh() -> None:
    control = create_log_refresh_control(key="test")
    assert control.name == "marimo-refresh"


def test_render_log_panel_accepts_refresh(tmp_path: pathlib.Path) -> None:
    log_file = tmp_path / "log.txt"
    log_file.write_text("line one\nline two")
    control = create_log_refresh_control(key="test-render")

    panel = render_log_panel(
        log_file,
        refresh_control=control,
        refresh_ticks=0,
    )

    assert "line two" in panel._repr_html_()
