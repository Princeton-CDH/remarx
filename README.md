<!-- --8<-- [start:overview] -->

# remarx

This repository contains in-progress research software developed for the CDH project
[Citing Marx](https://cdh.princeton.edu/projects/citing-marx/).
The primary purpose of this software is to identify quotes of Karl Marx's _Manifest
der Kommunistischen Partei_ and the first volume of _Das Kapital_ within articles
published in _Die Neue Zeit_ between 1891 and 1918.

[![Unit Tests](https://github.com/Princeton-CDH/remarx/actions/workflows/unit_tests.yml/badge.svg)](https://github.com/Princeton-CDH/remarx/actions/workflows/unit_tests.yml)

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
uv venv
```

#### Install `remarx`

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

### Closing quote finder app

The app will not close automatically when you close the browser window or tab.
To close the app:

1. Type control+c within the terminal where the `remarx-app` command was run
1. Then, when prompted, type `y` followed by enter.

## Documentation

Find public documentation at: [remarx Documentation](https://princeton-cdh.github.io/remarx/)

<!-- --8<-- [end:overview] -->

## Development

For development setup, documentation generation, and contributing guidelines, see [Developer Notes](DEVELOPERNOTES.md).

## License

This project is licensed under the [Apache 2.0 License](LICENSE).

(c)2025 Trustees of Princeton University. Permission granted for non-commercial
distribution online under a standard Open Source license.
