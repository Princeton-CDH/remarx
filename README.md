# Citing Marx - Experiment 3: Embeddings

This is work associated with the CDH project [Citing Marx](https://cdh.princeton.edu/projects/citing-marx)

## Pretrained text embeddings experiments

This branch contains code and data for preliminary experiments
using language model embeddings to identify similar sentences
(quotation detection) and differentiate word tokens (title detection).

### Contents

- `data/`
  - `annotation_quotation_citations.csv` : Recogito annotation data for four quotes from two articles with identified citations for the quotation
  - `dnz-sample-articles/`: text files for two sample articles annotated with quotes that have known citations
  - `mega-sample-pages/`: text files for 4 pages of MEGA cited in the two sample articles; extracted from MEGA TEI xml file with `tei_page.py` script
  - `sentence-corpora/` : JSON lines files with sentence corpora for dnz articles and mega pages; created with `build_sentence_corpus.py` script
  - `sentence-embeddings/` : pickled numpy arrays of embeddings data for the sentence corpora files; created by `get_sentence_embeddings.py` script
- `src/remarx/`: python package with utility code and scripts
   - `build_sentence_corpus.py`: script to parse a directory of text files into a JSONL corpus of sentences; uses Stanza for sentence splitting; adapted from experiment 2 with very light modification
   - `get_sentence_embeddings.py` : script to build and save sentence-level embeddings for a sentence-level corpus
   - `tei_page.py` : script to extract save TEI content between two pages as plain text