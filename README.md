# Citing Marx - Experiment 2: Traditional NLP

This is work associated with the CDH project [Citing Marx](https://cdh.princeton.edu/projects/citing-marx/)

## Traditional NLP experiments

This branch contains code and data for preliminary experiments using
traditional NLP approaches and out-of-the-box software to identify
titles and quotations in sample text content from the Citing Marx project.


## Development Instructions

### Developer setup and installation
- **Recommended:** create a python virtual environment with your tool of choice (virtualenv, conda, etc); use python 3.12 or higher

- Install the local checked out version of this package in editable mode (`-e`), including all python dependencies and optional dependencies for development and testing:

```sh
pip install -e ".[dev]"
```

- This repository uses [pre-commit](https://pre-commit.com/) for python code linting and consistent formatting. Run this command to initialize and install pre-commit hooks:

```sh
pre-commit install
```