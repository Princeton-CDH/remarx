"""
Utility functions for marimo notebooks
"""

import marimo as mo
from openai.types.chat import ChatCompletion


def display_bracketed_response(response: ChatCompletion) -> mo.Html:
    """
    Display the response of a model where the response includes square
    bracket annotations. Text within square brackets is highlighted and
    the square brackets removed.
    """
    # Assume the respose contains a single output
    output_object = response.choices[0]
    # Check finish reason
    finish_reason = output_object.finish_reason
    if finish_reason == "length":
        print("WARNING: Response stopped early due to length limits!")
    elif finish_reason == "content_filter":
        print("WARNING: Content filtering occurred for response!")

    # Display reponse
    output_text = output_object.message.content
    output_text = output_text.replace("[", "<mark>")
    output_text = output_text.replace("]", "</mark>")
    return mo.md(output_text)
