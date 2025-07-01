def highlight_spans(text: str, spans: list[tuple]) -> str:
    # method to add <mark> highlighting for one or more spans within a text string
    # takes text and string with one or more spans in a format that can be parsed by intspan
    # returns the text with <mark> tags around the highlighted regions
    previous_end = 0
    text_parts = []
    for start, end in spans:
        # text before the mark
        text_parts.append(text[previous_end:start])
        # text to be highlighted
        text_parts.append(f"<mark>{text[start:end]}</mark>")
        # set previous end to the portion after this span
        previous_end = end
    # append any text after the last highlighted portion
    text_parts.append(text[previous_end:])
    return "".join(text_parts)
