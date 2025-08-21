"""MkDocs hooks."""

import ast
from pathlib import Path
from typing import Any

import mkdocs_gen_files


def get_module_docstring(module_path: Path) -> str:
    """Extract the module docstring from a Python file."""
    try:
        with module_path.open(encoding="utf-8") as f:
            tree = ast.parse(f.read())

        # Get the first string literal as module docstring
        if (
            tree.body
            and isinstance(tree.body[0], ast.Expr)
            and isinstance(tree.body[0].value, ast.Constant)
            and isinstance(tree.body[0].value.value, str)
        ):
            return tree.body[0].value.value.strip()
    except Exception:
        pass
    return "No description available"


def scan_modules(src_path: Path) -> list[dict[str, str]]:
    """Scan the source directory for Python modules and extract their info."""
    modules = []

    # Find all __init__.py files to identify packages
    for init_file in src_path.rglob("__init__.py"):
        if init_file.parent == src_path:
            continue  # Skip the root __init__.py

        # Calculate relative module path
        rel_path = init_file.parent.relative_to(src_path)
        module_name = str(rel_path).replace("/", ".")

        # Get docstring
        docstring = get_module_docstring(init_file)
        if docstring == "No description available":
            continue

        # Create relative link to documentation page
        doc_link = f"{rel_path.name}.md"

        modules.append({"name": module_name, "docstring": docstring, "link": doc_link})

    # Also scan for standalone .py files (app.py, etc.) that have docstrings
    for py_file in src_path.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue

        # Calculate relative module path
        rel_path = py_file.relative_to(src_path)
        module_parts = [*list(rel_path.parts[:-1]), rel_path.stem]
        module_name = ".".join(module_parts)

        # Get docstring
        docstring = get_module_docstring(py_file)
        if docstring == "No description available":
            continue

        # For submodules, link to the parent module page
        if len(module_parts) > 1:
            parent_name = module_parts[0]
            doc_link = f"{parent_name}.md"
        else:
            doc_link = f"{module_parts[0]}.md"

        modules.append({"name": module_name, "docstring": docstring, "link": doc_link})

    return sorted(modules, key=lambda x: x["name"])


def generate_api_index(config: dict[str, Any]) -> None:
    """Generate the API documentation index with module table."""
    project_root = Path(config["config_file_path"]).parent
    src_path = project_root / "src" / "remarx"

    if not src_path.exists():
        return

    # Scan for modules
    modules = scan_modules(src_path)

    if not modules:
        return

    # Generate the index content
    index_content = ["# Overview", ""]
    index_content.append("")

    # Create the table
    index_content.append("| Module | Description |")
    index_content.append("|--------|-------------|")

    for module in modules:
        description = " ".join(
            line.strip() for line in module["docstring"].split("\n") if line.strip()
        )
        # Escape any pipe characters in the description (just in case)
        description = description.replace("|", "\\|")
        index_content.append(
            f"| [{module['name']}]({module['link']}) | {description} |"
        )

    # Write the generated content using mkdocs-gen-files
    with mkdocs_gen_files.open("api/index.md", "w") as f:
        f.write("\n".join(index_content))


def on_files(files: list, config: dict[str, Any]) -> list:
    """Generate files during the build process."""
    generate_api_index(config)
    return files
