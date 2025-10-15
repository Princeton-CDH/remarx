# CHANGELOG

## 0.2.0

### Application

- The app now consists of two notebooks (Sentence Corpus Builder & Quote Finder)
- Logging is now automatically configured by the application, and the log file location is reported to the user
- Quote Finder notebook now supports quotation detection between two sentence corpus files (original and reuse)

### Documentation

- Add technical design document to MkDocs documentation

### Sentence corpus creation

- Add sentence id field (`sent_id`) to generated sentence corpora
- Processes TEI/XML documents to yield separate chunks for body text and footnotes, with each footnote yielded individually as a separate element

### Quotation detection

- Add a method for generating sentence embeddings from a list of sentences
- Added method for identifying likely quote sentence pairs

### Scripts

- Add `parse_html` script for converting the manifesto html files to plain text for sentence corpus input (one-time use)

### Misc

- Add a utility method (`configure_logging`) to configure logging, supporting logging to a file or to stdout

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
