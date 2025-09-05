# CHANGELOG

## 0.2.0

### Application

- Add corpus CSV uploading interface for the quotation detection step

## 0.1.0

### Sentence Module

- Add `segment_text` function for breaking text into sentences with character-level indices
- Add `corpus` submodule with:
    - Input classes for text and TEI/XML
    - A factory method to initialize appropriate input class based on file type
    - A method and script for creating a sentence corpus
    - Processes TEI/XML documents to yield separate chunks for body text and footnotes, with each footnote yielded individually as a separate element

### Application

- Add initial application that can build sentence corpora for supported file types

### Documentation

- Set up Mkdocs for documentation
