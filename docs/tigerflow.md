# TigerFlow Pipeline

The `src/remarx/pipeline/` directory contains a [TigerFlow](https://github.com/Princeton-CDH/tigerflow)
pipeline for running sentence embedding at scale on a Slurm HPC cluster (e.g. Princeton's della).

## How it works

```
corpora/*.csv  →  [embed_sentences]  →  results/*.npy
```

Each CSV produced by `remarx-create-corpus` is embedded independently as a Slurm job.
The model loads once per worker in `setup()`, then `run()` is called once per file.

- Input: CSV with a `text` column (one sentence per row)
- Output: float32 array of shape `[num_sentences, 768]`, L2-normalized
- Model: `paraphrase-multilingual-mpnet-base-v2` (configurable)

## Running on della

1. Update `setup_commands` in `config.yaml` to activate your environment on the cluster.

2. Run the pipeline:

```bash
cd src/remarx/pipeline/

tigerflow run config.yaml \
  /path/to/corpora/ \
  /path/to/embeddings/
```

3. Monitor progress:

```bash
tigerflow report /path/to/embeddings/
```

## Local testing

Change `kind: slurm` to `kind: local` in `config.yaml` and remove the `max_workers`,
`worker_resources`, and `setup_commands` fields to run locally without Slurm.

## Output

For each `{name}.csv` input, the pipeline writes `{name}.npy` to the output directory.
Row order matches the source CSV:

```python
import numpy as np
import polars as pl

df = pl.read_csv("corpora/my_doc.csv")
embeddings = np.load("embeddings/my_doc.npy")
# embeddings[i] is the vector for df["text"][i]
```

These `.npy` files are compatible with `find_quote_pairs()` for downstream nearest-neighbor search.
