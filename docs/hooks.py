"""MkDocs hooks."""

from pathlib import Path
from typing import Any


def on_pre_build(config: dict[str, Any]) -> None:
    """
    Replace Developer Notes link in README.md before MkDocs builds the site.
    """
    # Get paths using pathlib
    project_root = Path(config["config_file_path"]).parent
    root_readme_path = project_root / "README.md"
    docs_readme_path = Path(config["docs_dir"]) / "index.md"

    # Read the original README from the root of the project
    content = root_readme_path.read_text(encoding="utf-8")

    # Replace GitHub links with MkDocs-compatible links
    content = content.replace(
        "[Developer Notes](DEVELOPERNOTES.md)", "[Developer Notes](devnotes.md)"
    )

    # Write the processed content to docs/index.md
    docs_readme_path.write_text(content, encoding="utf-8")
