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
    uv tool install pre-commit --with pre-commit-uv
    ```

- To run `pre-commit` explicitly run:

    ```
    uv tool run pre-commit
    ```

## Changelog

The `CHANGELOG.md` is meant for end users and should document user-facing changes only.
Internal changes like CI/CD updates, build system modifications, or development tooling
changes should not be included in the changelog unless it is substantial enough to potentially impact functionality, such as a major refactor.

### To Skip Changelog Check for Specific PRs

1. Add the `no changelog` label to your PR:

    - Via GitHub web interface: Go to your PR → Labels section in right sidebar → Click gear icon → Type "no changelog" and select it
    - Via GitHub CLI: Run `gh pr edit --add-label "no changelog"`

2. The changelog check will automatically re-run and pass when the label is applied

3. Remove the label if you later decide the PR does need a changelog entry

## Documentation

This project uses [MkDocs](https://www.mkdocs.org/) for documentation generation.

### Working with Documentation

Step 1: Build documentation locally

- run `uv run mkdocs build`

- Generates static site in `site/` directory

Step 2: Preview documentation locally

- run `uv run mkdocs serve`

- Opens at `http://127.0.0.1:8000/` and auto-reloads on file changes

### Writing Documentation

- Use MkDocs [snippets](https://pypi.org/project/mkdocs-snippets/) plugin (`--8<-- "filename"`) to include content from other files when needed.
- API docs are auto-generated from Python docstrings using [mkdocstrings](https://mkdocstrings.github.io/).

## Useful `uv` commands

- `uv add`: Add a new dependency to the project (i.e., updates `pyproject.toml`)
- `uv add --dev`: Add a new development dependency to the project
- `uv remove`: Remove a dependency from the project
- `uv remove --dev`: Remove a development dependency from the project
- `uv run`: Run a command or script
- `uv run marimo edit [notebook.py]`: Launch marimo notebook in edit mode
