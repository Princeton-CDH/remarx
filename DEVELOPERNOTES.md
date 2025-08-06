# Developer Notes

This repo uses [git-flow](https://github.com/nvie/gitflow) branching conventions;
**main** contains the most recent release, and work in progress will be on the
**develop** branch. Pull requests for new features should be made against develop.

### Developer setup and installation

- **Recommended:** Create a python virtual environment with your tool of choice
  (uv, mamba, venv, etc); use python 3.12.

- Install the local checked out version of this package in editable mode (`-e`),
  including all python dependencies and optional dependencies for development and testing:

```sh
# Using uv (recommended)
uv sync

# Or using pip
pip install -e ".[dev]"
```

- This repository uses [pre-commit](https://pre-commit.com/) for python code linting
  and consistent formatting. Run this command to initialize and install pre-commit hooks:

```sh
uv tool run pre-commit install
```
