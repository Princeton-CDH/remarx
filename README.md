<!-- --8<-- [start:overview] -->

# remarx

This repository contains in-progress research software developed for the CDH project
[Citing Marx](https://cdh.princeton.edu/projects/citing-marx/).
The primary purpose of this software is to identify quotes of Karl Marx's _Manifest
der Kommunistischen Partei_ and the first volume of _Das Kapital_ within articles
published in _Die Neue Zeit_ between 1891 and 1918.

[![PyPI - Version](https://img.shields.io/pypi/v/remarx)](https://pypi.org/project/remarx/)
[![Unit Tests](https://github.com/Princeton-CDH/remarx/actions/workflows/unit_tests.yml/badge.svg)](https://github.com/Princeton-CDH/remarx/actions/workflows/unit_tests.yml)
[![codecov](https://codecov.io/gh/Princeton-CDH/remarx/graph/badge.svg?token=waqNjbHV8d)](https://codecov.io/gh/Princeton-CDH/remarx)
[![Apache 2 License](https://img.shields.io/badge/license-Apache%20License%202.0-blue)](#license)

## Basic Usage

### Installation

Documentation assumes the use of `uv` for installing python and python packages, as
well as running python scripts. The first time you follow these instructions, you
should install `uv` per
[`uv` installation documentation](https://docs.astral.sh/uv/getting-started/installation/).
This only step only needs to be done once.

#### Create a `uv` environment

Create a new virtual environment using `uv`.

```
uv venv --python 3.12
```

#### Install `remarx`

To install the most recent release published on PyPIi:

```
uv pip install remarx
```

remarx as a python package directly from GitHub. Use a branch or tag name, e.g.
`@develop` or `@0.1` if you need to install a specific version.

```
uv pip install "remarx @ git+https://github.com/Princeton-CDH/remarx"
```

### Launch quote finder app

To launch the remarx quote finder application run the `remarx-app` command:

```
uv run remarx-app
```

### Default corpus directories

For convenience, we suggest saving and selecting corpus files from a standard location under your home directory: `~/remarx-data/corpora/original` and `~/remarx-data/corpora/reuse`. Both the Sentence Corpus Builder and Quote Finder portions of the app default to these folders (with an option to override) and prompt you to create them if they don't exist.

### Closing quote finder app

The app will not close automatically when you close the browser window or tab.
To close the app:

1. Type control+c within the terminal where the `remarx-app` command was run
2. Then, when prompted, type `y` followed by enter.

## Documentation

Find public documentation at: [remarx Documentation](https://princeton-cdh.github.io/remarx/)

<!-- --8<-- [end:overview] -->

## Development

For development setup, documentation generation, and contributing guidelines, see [Developer Notes](DEVELOPERNOTES.md).

## License

This project is licensed under the [Apache 2.0 License](LICENSE).

(c)2025 Trustees of Princeton University. Permission granted for non-commercial
distribution online under a standard Open Source license.
