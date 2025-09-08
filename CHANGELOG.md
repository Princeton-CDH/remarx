# CHANGELOG

## 0.2.0

### Scripts

- Add `parse_html` script for converting the manifesto html files to plain text for sentence corpus input (one-time use)

## 0.1.0

### Sentence Module

- Add `segment_text` function for breaking text into sentences with character-level indices
- Add `corpus` submodule with:
  - input classes for text and TEI/XML
  - a factory method to initialize appropriate input class based on file type
  - a method and script for creating a sentence corpus

### Application

- Add initial application that can build sentence corpora for supported file types

### Documentation

- Set up Mkdocs for documentation
