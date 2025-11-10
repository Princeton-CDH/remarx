import logging
import pathlib
from types import SimpleNamespace

from remarx.quotation import find_quotes


def make_paths(
    tmp_path: pathlib.Path,
) -> tuple[pathlib.Path, pathlib.Path, pathlib.Path]:
    original = tmp_path / "original.csv"
    reuse = tmp_path / "reuse.csv"
    output = tmp_path / "results" / "pairs.csv"
    return original, reuse, output


def test_run_find_quotes_calls_find_quote_pairs(monkeypatch, tmp_path):
    captured = SimpleNamespace(args=None)

    def fake_find_quote_pairs(*, original_corpus, reuse_corpus, out_csv):
        captured.args = (original_corpus, reuse_corpus, out_csv)
        return SimpleNamespace(
            embedding_seconds=1.0, index_seconds=2.0, query_seconds=3.0
        )

    monkeypatch.setattr(find_quotes, "find_quote_pairs", fake_find_quote_pairs)

    original, reuse, output_file = make_paths(tmp_path)

    output_path = find_quotes.run_find_quotes(original, reuse, output_file)

    assert captured.args == (original, reuse, output_path)
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


def test_run_find_quotes_benchmark_logs(monkeypatch, tmp_path, caplog):
    monkeypatch.setattr(
        find_quotes,
        "find_quote_pairs",
        lambda **_: SimpleNamespace(
            embedding_seconds=44.2, index_seconds=0.3, query_seconds=0.1
        ),
    )

    times = iter([100.0, 112.5])
    monkeypatch.setattr(find_quotes, "time", lambda: next(times))

    caplog.set_level(logging.INFO, logger=find_quotes.logger.name)

    original = tmp_path / "orig.csv"
    reuse = tmp_path / "reuse.csv"
    output_path = tmp_path / "out" / "pairs.csv"

    find_quotes.run_find_quotes(
        original_corpus=original,
        reuse_corpus=reuse,
        output_path=output_path,
        benchmark=True,
    )

    assert any("Benchmark summary" in record.getMessage() for record in caplog.records)
