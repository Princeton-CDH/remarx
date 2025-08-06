# remarx

This repository contains in-progress research software developed for the CDH project
[Citing Marx](https://cdh.princeton.edu/projects/citing-marx/).
The primary purpose of this software is to identify quotes of Karl Marx's _Manifest
der Kommunistischen Partei_ and the first volume of _Das Kapital_ within articles
published in _Die Neue Zeit_ between 1891 and 1918.

## Basic Usage

### Installation

Use [`uv`](https://docs.astral.sh/uv/getting-started/installation/) to install
remarx as a python package directly from GitHub. Use a branch or tag name, e.g.
`@develop` or `@0.1` if you need to install a specific version.

```
uv add "remarx @ git+https://github.com/Princeton-CDH/remarx"
```

### Launch remarx app (GUI)

To launch the remarx application run the `remarx-gui` command:

```
uv run remarx-gui
```

### Launch other notebooks as apps

To launch other `remarx` notebooks run the `remarx-nb` command with the
name of the notebook to be launched.

```
uv run remarx-nb remarx_gui
```

## License

This project is licensed under the [Apache 2.0 License](LICENSE).

(c)2025 Trustees of Princeton University. Permission granted for non-commercial
distribution online under a standard Open Source license.
