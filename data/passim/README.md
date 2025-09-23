# Passim data

This folder includes input and output content for a small-scale passim test to compare with other methods.

## Input data

The input file was created as follows:

- Used the corppa utility script `build_text_corpus.py`  to convert plain text pages to JSON lines:
```sh
python ../corppa/src/corppa/utils/build_text_corpus.py data/mega-sample-pages/ data/passim/mega_pages.jsonl
python ../corppa/src/corppa/utils/build_text_corpus.py data/dnz-sample-articles/ data/passim/dnz_articles.jsonl
```

- Used `jq` to add a series field:
```sh
jq -c '. + {"series": "mega"}' data/passim/mega_pages.jsonl > data/passim/mega_pages_corpus.jsonl
jq -c '. + {"series": "dnz"}' data/passim/dnz_articles.jsonl > data/passim/dnz_articles_corpus.jsonl
```

- Then used `jq` to combine them into a single json lines input document:
```sh
jq -c '.' data/passim/mega_pages_corpus.jsonl data/passim/dnz_articles_corpus.jsonl > data/passim/input.jsonl
```

## Output

The `output/default` directory includes the cluster results from running passim with defaults:


```sh
passim data/passim/input.jsonl data/passim/output/default/
```


### Notes

- Output NDJSON lives under `data/passim/output/default/out.json/` (Spark-style part files).
- Local run artifacts (e.g., `local-*/`, `run-*/`, `retry-*/`, `**/.crc`, `**/_SUCCESS`, `**/*.parquet`) are ignored via `data/passim/output/.gitignore` and should not be committed.
- Work tracked in issue [#221](https://github.com/Princeton-CDH/remarx/issues/221).

