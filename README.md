# remarx

This repository contains in-progress research software developed for the CDH project
[Citing Marx](https://cdh.princeton.edu/projects/citing-marx/).
The primary purpose of this software is to identify quotes of Karl Marx's *Manifest
der Kommunistischen Partei* and the first volume of *Das Kapital* within articles
published in *Die Neue Zeit* between 1891 and 1918.


## Development instructions

This repo uses [git-flow](https://github.com/nvie/gitflow) branching conventions;
**main** contains the most recent release, and work in progress will be on the
**develop** branch. Pull requests for new features should be made against develop.

### Developer setup and installation

- **Recommended:** Create a python virtual environment with your tool of choice
(uv, mamba, venv, etc); use python 3.12.

- Install the local checked out version of this package in editable mode (`-e`),
including all python dependencies  and optional dependencies for development and testing:
```sh
pip install -e ".[dev]"
```

#  TODO: Uncomment this section once pre-commit is set up
#  - This repository uses [pre-commit](https://pre-commit.com/) for python code linting
#  and consistent formatting. Run this command to initialize and install pre-commit hooks:
#  ```sh
#  pre-commit install
