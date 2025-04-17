# Citing Marx

This is work associated with the CDH project [Citing Marx](https://cdh.princeton.edu/projects/citing-marx/)

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

## AI Sandbox experiment

This branch contains code and data for preliminary experiments with
Princeton's AI Sandbox.


### Marimo notebook setup

The notebook for selecting direct quote annotations requires
that you manually add a copy of `1896-97aCLEAN.txt` to `/data/text/`.

Use `marimo` to run notebook:

```console
marimo edit notebooks/quote-data.py
```

This notebook has been configured to save Jupyter notebook snapshots for
viewing on GitHub.

