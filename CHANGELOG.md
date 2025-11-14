# CHANGELOG

## 0.4.0

### Sentence corpus creation

- ALTO input now uses block-level tags for filtering and section type in sentence corpus

    - By default, only includes blocks tagged as text, footnote, Title, or untagged

- TEI input revised and improved, now operates at paragraph level instead of page

    - Omits tables, math formulas, footnote references, and opening editorial introduction
    - Omits footnote labels (e.g., "1)", "2)") from footnote text
    - Converts newlines within paragraphs to whitespace; ensures lines are separated by whitespace
    - Handles sentences that cross pages when contained within a single paragraph tag
    - Excludes editorial content; includes all non-editorial text content
    - Yields all body content first followed by all footnotes
    - Improved parsing speed

### Quotation detection

- Add the `remarx-find-quotes` CLI script to run the quote finder, with a `--benchmark` flag to collect performance metrics
- Add consolidation logic to group quotes that are sequential in both original and reuse texts

### Application

- Display logging output in real-time to show progress when building corpus

## [0.3.0] - 2025-10-27

### Sentence corpus creation

- Sentence corpora generated from TEI now include line number field (`line_number`) based on line begin tag (`<lb>` n attribute)
- Support for ALTO XML input as a zipfile with multiple pages
    - Skips non-ALTO files, logs warnings for invalid or empty xml
    - Yields sentence corpora indexed across pages; ordering based on natural sort of filenames
- Improved logging output for `remarx-create-corpus` script, with optional verbose mode

## [0.2.0] - 2025-10-15

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
[0.2.0]: https://github.com/Princeton-CDH/remarx/tree/0.2
[0.3.0]: https://github.com/Princeton-CDH/remarx/tree/0.3
