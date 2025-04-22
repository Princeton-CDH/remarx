"""
Utility functions for marimo notebooks
"""

import re

import marimo as mo


def has_closed_brackets(text: str):
    """
    Checks if a text's possibly nested square bracket expressions are
    all properly closed (e.g., `[hello] [wo[rl]d]!")
    """
    # Return early if text does not contain square bracket characters
    if "[" not in text and "]" not in text:
        return True

    # Iteratively remove unnested square bracket strings
    unnested_exp = r"\[[^][]*\]"
    unnested_re = re.compile(unnested_exp)
    prev_str = text
    new_str = unnested_re.sub("", text)
    while prev_str != new_str:
        prev_str = new_str
        new_str = unnested_re.sub("", prev_str)

    # Check if brackets characters are present
    # If true then the string contains an unclosed bracket expression
    return "[" not in new_str and "]" not in new_str


def highlight_bracketed_text(text: str) -> mo.Html:
    """
    Display text as markdown with square bracketed expressions highlighted
    and the square brackets removed.

    Raises ValueError if square brackets are not properly closed.
    """
    # Check brackets
    if not has_closed_brackets(text):
        raise ValueError("Response contains an improperly closed bracket")

    # "Display" text as markdown
    output_text = text.replace("[", "<mark>")
    output_text = output_text.replace("]", "</mark>")
    return mo.md(output_text)
