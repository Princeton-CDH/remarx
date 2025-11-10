import logging
import pathlib
from dataclasses import dataclass

from remarx.quotation import find_quotes


@dataclass
class FakeMetrics:
    embedding_seconds: float
    index_seconds: float
    query_seconds: float


def test_run_find_quotes_calls_find_quote_pairs(monkeypatch, tmp_path):
    captured = {}

    def fake_find_quote_pairs(*, original_corpus, reuse_corpus, out_csv):
        captured["args"] = (original_corpus, reuse_corpus, out_csv)
        return FakeMetrics(1.0, 2.0, 3.0)

    monkeypatch.setattr(find_quotes, "find_quote_pairs", fake_find_quote_pairs)

    original = tmp_path / "original.csv"
    reuse = tmp_path / "reuse.csv"
    output_file = tmp_path / "results" / "pairs.csv"

    output_path = find_quotes.run_find_quotes(original, reuse, output_file)

    assert captured["args"] == (original, reuse, output_path)
    assert output_path == output_file
    assert output_file.parent.is_dir()


def test_main_configures_logging_and_passes_flags(monkeypatch, tmp_path):
    logged = {}

    def fake_configure_logging(stream, log_level):
        logged["stream"] = stream
        logged["log_level"] = log_level

    called = {}

    def fake_run_find_quotes(
        original_corpus,
        reuse_corpus,
        output_path,
        *,
        benchmark,
    ):
        called["args"] = (original_corpus, reuse_corpus, output_path)
        called["benchmark"] = benchmark

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

    assert logged["log_level"] == logging.DEBUG
    assert called["benchmark"] is True
    assert called["args"][0] == pathlib.Path(argv[1])
    assert called["args"][2] == pathlib.Path(argv[3])


def test_run_find_quotes_benchmark_logs(monkeypatch, tmp_path, caplog):
    monkeypatch.setattr(
        find_quotes,
        "find_quote_pairs",
        lambda **_: FakeMetrics(44.2, 0.3, 0.1),
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
