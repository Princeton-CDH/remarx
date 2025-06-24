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
  - `mega-sample-pages/`: text files for selected pages of MEGA cited in the two sample articles (includes one 2-page span without footnotes); extracted from MEGA TEI xml file with `tei_page.py` script
  - `sentence-corpora/` : JSON lines files with sentence corpora for DNZ articles and MEGA pages; created with `build_sentence_corpus.py` script
    - `title-mentions-sentences.jsonl`: JSONL lines file version of `title_mentions_sent_results.csv` from Experiment II.
  - `sentence-embeddings/` : binary `.npy` files containing pickled numpy arrays of embeddings data for the sentence corpora files; created by `get_sentence_embeddings.py` script
  - `sentence-eval-pairs/`: CSV files with sentences from sample articles and corresponding sentences from MEGA pages, for use in evaluation of similar sentence retrieval methods
    - `dnz_marx_sentence_pairs.csv`: CSV file with MEGA/DNZ sentence pairs from sample quotations, for use in evaluating methods; reviewed by and includes notes from project team members
      for use in evaluation of similar sentence retrieval methods
  - `sentence-pairs/`: data files containing top sentence pair results for various approximate nearest neighbor methods
  - `token-embeddings/`: token embedding files (`.npy` & `.csv`) for `title-mentions-sentences.jsonl`; created by `get_token_embeddings.py` script
- `src/remarx/`: python package with utility code and scripts
  - `build_sentence_corpus.py`: script to parse a directory of text files into a JSONL corpus of sentences; uses Stanza for sentence splitting; adapted from experiment 2 with very light modification
  - `get_sentence_embeddings.py` : script to build and save sentence-level embeddings for a sentence-level corpus
  - `get_token_embeddings.py`: script to build and save token-level embeddings for a specific term for a sentence-level corpus
  - `tei_page.py` : script to extract and save TEI content between two or more pages as plain text
- `notebooks/`: marimo notebooks for exploration and data work
  - `quotation-sentence-ids.py`: notebook to filter candidate sentence ids for DNZ/MEGA sentence pairs for evaluation
  - `try-chroma.py`: notebook trying out ChromaDB to find similar sentences and compare with evaluation sentence pairs
  - `try-cross-encoder.py`: notebook investigating the usage of a cross encoder model for identifiying similar sentences
