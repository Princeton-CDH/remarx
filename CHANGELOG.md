# CHANGELOG

## 0.2.0

### Application

- Add a sentence corpus selection interface for the quotation detection step

### Documentation

- Add technical design document to MkDocs documentation

### Sentence corpus creation

- Processes TEI/XML documents to yield separate chunks for body text and footnotes, with each footnote yielded individually as a separate element
- Add a method for generating sentence embeddings from sentence corpus

### Scripts

- Add `parse_html` script for converting the manifesto html files to plain text for sentence corpus input (one-time use)

## [0.1.0] - 2025-09-08

_Initial release._

### Sentence corpus creation

- Add `segment_text()` function for splitting plain text into sentences with character-level indices
- Add support for plain text files as input
- Add preliminary support for TEI XML files as corpus input; includes page numbers, assumes MEGA TEI
- Add factory method to initialize appropriate input class for supported file types
- Add `create_corpus()` function to generate a sentence corpus CSV from a single supported input file
- Add command line script `remarx-create-corpus` to input a supported file and generate a sentence corpus

### Application

- Add preliminary application with access to sentence corpus creation for supported file types
- Add command line script to launch application

### Documentation

- Document package installation (README)
- Set up MkDocs for code documentation
- Add GitHub Actions workflow to build and deploy documentation to GitHub Pages for released versions (`main` branch)

### Misc

- Add GitHub Actions workflow to build and publish python package on PyPI when a new GitHub release created

[0.1.0]: https://github.com/Princeton-CDH/remarx/tree/0.1
