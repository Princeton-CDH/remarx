# Developer Notes

This repo uses [git-flow](https://github.com/nvie/gitflow) branching conventions;
**main** contains the most recent release, and work in progress will be on the
**develop** branch. Pull requests for new features should be made against develop.

## Developer setup and installation

**Note:** While the usage of [`uv`](https://docs.astral.sh/uv/) is assumed, this
package is also compatible with the use of `pip` for python package management and
a tool of your choice for creating python virtual environments (`mamba`, `venv`, etc).

- Install `uv` if it's not already installed. `uv` can be installed via
  [Homebrew](https://docs.astral.sh/uv/getting-started/installation/#homebrew) or a
  [standalone installer](https://docs.astral.sh/uv/getting-started/installation/#standalone-installer).
  See uv's installation [documentation](https://docs.astral.sh/uv/getting-started/installation/#installing-uv)
  for more details.

- To explicitly sync the project's dependencies, including optional dependencies
  for development and testing, to your local environment run:

```
uv sync
```

- Note that `uv` performs syncing and locking automatically (e.g., any time `uv run`
  is invoked). By default, syncing will remove any packages not specified in the
  `pyproject.toml`.

- This repository uses [pre-commit](https://pre-commit.com/) for python code linting
  and consistent formatting. Run this command to initialize and install pre-commit hooks:

```
uv tool run pre-commit install
```

## Useful `uv` commands

- `uv add`: Add a new dependency to the project (i.e., updates `pyproject.toml`)
- `uv add --dev`: Add a new development dependency to the project
- `uv remove`: Remove a dependency from the project
- `uv remove --dev`: Remove a development dependency from the project
- `uv run`: Run a command or script
- `uv run marimo edit [notebook.py]`: Launch marimo notebook in edit mode
