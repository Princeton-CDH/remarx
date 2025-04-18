# this will likely change or be unnecessary pending revisions to our prompts,
# but my early experiments were only returning the quotes
# and they sometimes come back modified so can't be found exactly


def get_span_indices(context, span_text):
    start_index = end_index = None
    if span_text in context:
        start_index = context.find(span_text)
    if start_index is None:
        context_nonl = context.replace("\n", " ")
        if span_text in context_nonl:
            start_index = context_nonl.find(span_text)
    # if exact match wasn't found, identify by begin/end
    if start_index is None:
        first_chunk = span_text[:15]
        last_chunk = span_text[-15:]

        if first_chunk in context and last_chunk in context:
            start_index = context.find(first_chunk)
            end_index = context.find(last_chunk) + len(last_chunk)

    if start_index is not None:
        if end_index is None:
            end_index = start_index + len(span_text)
        return (start_index, end_index)
    return (None, None)
