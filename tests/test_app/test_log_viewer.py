import pathlib

import pytest

from remarx.app.log_viewer import read_log_tail


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
