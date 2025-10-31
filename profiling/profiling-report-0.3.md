# Profiling Report for Release 0.3's Sentence Corpus Builder (TEI & ALTO)

This branch profiled Release 0.3's Sentence Corpus Builder, comparing three sentence segmentation pipelines:

1. `stanza` (Baseline)
- Use the orginal `stanza` pipeline as baseline, which creates a new Stanza pipeline on every call to `segment_text()`.
- Performance: Slowest.

2. `stanza_optimized` (avoid reloading)
- Optimized the orginal `stanza` pipeline with caching to avoid repeated pipeline initialization overhead.
- Performance: Faster than baseline (see metrics in the table below).

3. `flair_spacy_de` (replace `stanza` with `flairNLP` using `spaCy`'s German model)
- Use `flairNLP`'s sentence splitter with `spaCy`'s `de_core_news_sm` model
- Performance: Fastest. But the corpus output looks quite different from `stanza`'s result. I haven't got a chance to carefully evaluate that.

#### Files used to run profiling
- TEI: MEGA_A2_B005-00_ETX (655 pages)
- ALTO: 1896-97a DNZ (836 files; 835 ALTO)

#### Results table

1. TEI

| Segmenter | CPU Time (log) | Wall Time | Profile | Speedup vs Baseline |
|---------|----------------|-----------|---------|---------------------|
| **Stanza Baseline** | ~281.2 s | ~337.0 s | `profile_tei.html` | — |
| **Stanza Optimized** | ~292.2 s | ~308.2 s | `profile_tei_stanza_optimized.html` | **8.5% faster** |
| **Flair** | — | ~273.5 s | `profile_tei_flair.html` | **18.8% faster** |


2. ALTO

| Segmenter | CPU Time (log) | Wall Time | Profile | Speedup vs Baseline |
|---------|----------------|-----------|---------|---------------------|
| **Stanza Baseline** | ~196.9 s | ~156.2 s | `profile_alto.html` | — |
| **Stanza Optimized** | ~151.1 s | ~152.8 s | `profile_alto_stanza_optimized.html` | **23.3% faster (CPU)** / **2.2% faster (wall)** |
| **Flair** | — | ~76.2 s | `profile_alto_flair.html` | **51.2% faster** |


---

### To View Profiling Results

1. `HTML` Visualizations generated with `pyinstrument` (hierarchical views of where wall-clock time is spent)

```bash
open profiling/wall\ time/profile_tei_flair.html
open profiling/wall\ time/profile_alto_flair.html
```

2. CPU Profiles generated with `cProfile` (`.prof` files contain CPU profiling data)

```bash
cd profiling/CPU\ time/

# View with built-in pstats (text output)
python -m pstats profile_tei.prof
# Then in interactive mode:
# >>> sort cumtime
# >>> stats 20

# Or generate visual reports with snakeviz
pip install snakeviz
snakeviz profile_tei.prof
# Opens interactive visualization in browser
```

**Key metrics in cProfile:**
- **tottime**: Total time spent in function (excluding subfunctions)
- **cumtime**: Cumulative time (including subfunctions)
- **ncalls**: Number of times function was called
- **percall**: Average time per call


---

#### Commands used

**Test files:**
- `TEI_FILE=~/remarx_test_files/input/Das_Kapital_MEGA_A2_B005-00_ETX.xml`
- `ALTO_ZIP=~/remarx_test_files/input/1896-97a\ XML\ Output-835pages.zip`

**Stanza Baseline (CPU time):**
```bash
uv run python -m cProfile -o "profiling/CPU time/profile_tei.prof" -m remarx.sentence.corpus.create "$TEI_FILE" profiling/output_corpus_csv/tei_sentences_stanza.csv
uv run python -m cProfile -o "profiling/CPU time/profile_alto.prof" -m remarx.sentence.corpus.create "$ALTO_ZIP" profiling/output_corpus_csv/alto_sentences_stanza.csv
```

**Stanza Baseline (Wall time):**
```bash
uv run python -m pyinstrument -r html -o "profiling/wall time/profile_tei.html" -m remarx.sentence.corpus.create "$TEI_FILE" profiling/output_corpus_csv/tei_sentences_stanza.csv
uv run python -m pyinstrument -r html -o "profiling/wall time/profile_alto.html" -m remarx.sentence.corpus.create "$ALTO_ZIP" profiling/output_corpus_csv/alto_sentences_stanza.csv
```

**Stanza Optimized (CPU time):**
```bash
uv run python -m cProfile -o "profiling/CPU time/profile_tei_stanza_optimized.prof" -m remarx.sentence.corpus.create --segmenter stanza_optimized "$TEI_FILE" profiling/output_corpus_csv/tei_sentences_stanza_optimized.csv
uv run python -m cProfile -o "profiling/CPU time/profile_alto_stanza_optimized.prof" -m remarx.sentence.corpus.create --segmenter stanza_optimized "$ALTO_ZIP" profiling/output_corpus_csv/alto_sentences_stanza_optimized.csv
```

**Stanza Optimized (Wall time):**
```bash
uv run python -m pyinstrument -r html -o "profiling/wall time/profile_tei_stanza_optimized.html" -m remarx.sentence.corpus.create --segmenter stanza_optimized "$TEI_FILE" profiling/output_corpus_csv/tei_sentences_stanza_optimized.csv
uv run python -m pyinstrument -r html -o "profiling/wall time/profile_alto_stanza_optimized.html" -m remarx.sentence.corpus.create --segmenter stanza_optimized "$ALTO_ZIP" profiling/output_corpus_csv/alto_sentences_stanza_optimized.csv
```

**Flair (Wall time):**
```bash
uv run python -m pyinstrument -r html -o "profiling/wall time/profile_tei_flair.html" -m remarx.sentence.corpus.create --segmenter flair_spacy_de "$TEI_FILE" profiling/output_corpus_csv/tei_sentences_flair.csv
uv run python -m pyinstrument -r html -o "profiling/wall time/profile_alto_flair.html" -m remarx.sentence.corpus.create --segmenter flair_spacy_de "$ALTO_ZIP" profiling/output_corpus_csv/alto_sentences_flair.csv
```
