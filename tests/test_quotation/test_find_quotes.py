import logging
import pathlib

from remarx.quotation import find_quotes
from remarx.quotation.pairs import QuoteDetectionMetrics


def test_run_find_quotes_calls_find_quote_pairs(monkeypatch, tmp_path):
    captured = {}

    def fake_find_quote_pairs(*, original_corpus, reuse_corpus, out_csv):
        captured["args"] = (original_corpus, reuse_corpus, out_csv)
        return QuoteDetectionMetrics(1.0, 2.0, 3.0)

    monkeypatch.setattr(find_quotes, "find_quote_pairs", fake_find_quote_pairs)

    original = tmp_path / "original.csv"
    reuse = tmp_path / "reuse.csv"
    output_dir = tmp_path / "results"

    output_path = find_quotes.run_find_quotes(original, reuse, output_dir)

    assert captured["args"] == (original, reuse, output_path)
    assert output_path == output_dir / find_quotes.DEFAULT_OUTPUT_FILENAME
    assert output_dir.is_dir()


def test_main_configures_logging_and_passes_flags(monkeypatch, tmp_path):
    logged = {}

    def fake_configure_logging(stream, log_level):
        logged["stream"] = stream
        logged["log_level"] = log_level

    called = {}

    def fake_run_find_quotes(original_corpus, reuse_corpus, output_dir, *, benchmark):
        called["args"] = (original_corpus, reuse_corpus, output_dir)
        called["benchmark"] = benchmark

    monkeypatch.setattr(find_quotes, "configure_logging", fake_configure_logging)
    monkeypatch.setattr(find_quotes, "run_find_quotes", fake_run_find_quotes)

    argv = [
        "remarx-find-quotes",
        str(tmp_path / "orig.csv"),
        str(tmp_path / "reuse.csv"),
        str(tmp_path / "out"),
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
        lambda **_: QuoteDetectionMetrics(44.2, 0.3, 0.1),
    )

    times = iter([100.0, 112.5])
    monkeypatch.setattr(find_quotes, "time", lambda: next(times))

    caplog.set_level(logging.INFO, logger=find_quotes.logger.name)

    original = tmp_path / "orig.csv"
    reuse = tmp_path / "reuse.csv"
    output_dir = tmp_path / "out"

    find_quotes.run_find_quotes(
        original_corpus=original,
        reuse_corpus=reuse,
        output_dir=output_dir,
        benchmark=True,
    )

    assert any("Benchmark summary" in record.getMessage() for record in caplog.records)
