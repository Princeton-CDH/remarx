import logging
import pathlib
from types import SimpleNamespace

from remarx.quotation import find_quotes


def test_run_find_quotes_calls_find_quote_pairs(monkeypatch, tmp_path):
    captured = SimpleNamespace(args=None)

    def fake_find_quote_pairs(*, original_corpus, reuse_corpus, out_csv, benchmark):
        captured.args = (original_corpus, reuse_corpus, out_csv, benchmark)

    monkeypatch.setattr(find_quotes, "find_quote_pairs", fake_find_quote_pairs)

    original = tmp_path / "original.csv"
    reuse = tmp_path / "reuse.csv"
    output_file = tmp_path / "results" / "pairs.csv"

    output_path = find_quotes.run_find_quotes(original, reuse, output_file)
    assert captured.args == (original, reuse, output_file, False)

    output_path = find_quotes.run_find_quotes(
        original, reuse, output_file, benchmark=True
    )
    assert captured.args == (original, reuse, output_file, True)
    assert output_path == output_file
    assert output_file.parent.is_dir()


def test_main_configures_logging_and_passes_flags(monkeypatch, tmp_path):
    logged = SimpleNamespace(stream=None, log_level=None)

    def fake_configure_logging(stream, log_level):
        logged.stream = stream
        logged.log_level = log_level

    called = SimpleNamespace(args=None, benchmark=None)

    def fake_run_find_quotes(
        original_corpus,
        reuse_corpus,
        output_path,
        *,
        benchmark,
    ):
        called.args = (original_corpus, reuse_corpus, output_path)
        called.benchmark = benchmark

    monkeypatch.setattr(find_quotes, "configure_logging", fake_configure_logging)
    monkeypatch.setattr(find_quotes, "run_find_quotes", fake_run_find_quotes)

    argv = [
        "remarx-find-quotes",
        str(tmp_path / "orig.csv"),
        str(tmp_path / "reuse.csv"),
        str(tmp_path / "out" / "pairs.csv"),
        "--verbose",
        "--benchmark",
    ]

    monkeypatch.setattr(find_quotes.sys, "argv", argv)

    find_quotes.main()

    assert logged.log_level == logging.DEBUG
    assert called.benchmark is True
    assert called.args[0] == pathlib.Path(argv[1])
    assert called.args[2] == pathlib.Path(argv[3])
