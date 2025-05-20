import marimo

__generated_with = "0.13.11"
app = marimo.App(
    width="full",
    app_title="Compare quotation detection methods",
    css_file="highlight.css",
)


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""# Compare quotation detection results in context""")
    return


@app.cell
def _():
    import polars as pl
    return (pl,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r""" """)
    return


@app.cell
def _(mo, pl):
    # Load data
    #
    # Load seq2seq quotes output, and previously calculated offset adjustment to annotated file.

    # public locaiton for compilation to wasm
    seq2seq_quotes_file = mo.notebook_location() / "public" / "seq2seq_quotes.csv"

    quotes_df = pl.read_csv(str(seq2seq_quotes_file))

    input_offset_file = (
        mo.notebook_location() / "public" / "seq2seq_input_offsets.csv"
    )
    input_offset_df = pl.read_csv(str(input_offset_file))

    # join seq2seq quotes data with input file offsets so we can calculate offset in the annotated file
    quotes_source_text = quotes_df.join(input_offset_df, on="file")
    return quotes_df, quotes_source_text


@app.cell
def _(pl, quotes_source_text):
    # adjust offsets to match annotated file
    from intspan import intspan


    # use intspan to parse and adjust by file offset and then serialize back to a span
    def adjust_span_offset(span, adjustment):
        span = intspan(
            span.replace(";", ",")
        )  # replace ; with , so intspan can parse ranges
        # adjust all values
        adjusted_span = intspan([i + adjustment for i in list(span)])
        return str(adjusted_span)


    # use intspan to parse and get first offset value
    def first_offset(span):
        return list(intspan(span))[0]


    # df.select([pl.struct(["ham", "spam", "foo"]).apply(my_complicated_function)])

    # start with quote offsets and then figure out which others we need
    adjusted_offsets = quotes_source_text.select(
        pl.col("quote_offsets", "file_offset")
    ).map_rows(
        lambda row: adjust_span_offset(row[0], row[1]), return_dtype=pl.String
    )

    quotes_adjusted = quotes_source_text.with_columns(
        quote_offsets_adjusted=pl.Series(adjusted_offsets),
        quote_offset_start=pl.Series(adjusted_offsets).map_elements(
            first_offset, return_dtype=pl.Int32
        ),
    )
    return adjust_span_offset, intspan, quotes_adjusted


@app.cell
def _(mo, pl):
    # load quote annotations test subset
    # - filter to the file we ran seq2seq on

    # direct_quotes_subset_file = "data/direct_quotes_subset.csv"
    direct_quotes_subset_file = (
        mo.notebook_location() / "public" / "direct_quotes_subset.csv"
    )

    quote_annotations = pl.read_csv(str(direct_quotes_subset_file)).filter(
        pl.col("FILE").eq("1896-97aCLEAN.txt")
    )
    return (quote_annotations,)


@app.cell
def _(pl, quote_annotations):
    # get a unique list of pages from quote annotations (some pages have multiple quotes)
    annotation_pages = quote_annotations.select(
        pl.col("page_index", "page_text", "page_start", "page_end")
    ).unique()
    return (annotation_pages,)


@app.cell(hide_code=True)
def _(adjust_span_offset, annotation_pages, pl, quotes_adjusted):
    # do a conditional join of annotation pages with seq2seq quotes to find pages where we have data from both methods for comparison
    quotes_pages = quotes_adjusted.join_where(
        annotation_pages,
        pl.col("quote_offset_start") >= pl.col("page_start"),
        pl.col("quote_offset_start") < pl.col("page_end"),
    )

    # adjust quote offset to make them relative to the page using page start
    page_offsets = quotes_pages.select(
        pl.col("quote_offsets_adjusted", "page_start")
    ).map_rows(lambda row: adjust_span_offset(row[0], -row[1]))

    quotes_pages = quotes_pages.with_columns(
        quote_offsets_page=pl.Series(page_offsets)
    ).sort("quote_offset_start")  # sort by order in the file
    return (quotes_pages,)


@app.cell
def _(intspan):
    def highlight_spans(text: str, spans: str) -> str:
        # method to add <mark> highlighting for one or more spans within a text string
        # takes text and string with one or more spans in a format that can be parsed by intspan
        # returns the text with <mark> tags around the highlighted regions
        spans = intspan(spans)
        previous_end = 0
        text_parts = []
        for start, end in spans.ranges():
            # text before the mark
            text_parts.append(text[previous_end:start])
            # text to be highlighted
            text_parts.append(f"<mark>{text[start:end]}</mark>")
            # set previuos end to the portion after this span
            previous_end = end
        # append any text after the last highlighted portion
        text_parts.append(text[previous_end:])
        return "".join(text_parts)
    return (highlight_spans,)


@app.cell
def _(highlight_spans, mo, quote_slider, quotes_pages):
    def display_seq2seq_page(quote):
        quote_info = {
            field: quote[field]
            for field in ["type", "speaker", "cue", "addressee"]
            if quote[field]
        }
        quote_info_string = (
            "<dl>"
            + " ".join(
                f"<dt>{field}</dt><dd>{value}</dd>"
                for field, value in quote_info.items()
            )
            + "</dl>"
        )

        return mo.Html(
            "<section class='page'><header><h1>seq2seq quote</h2>"
            + quote_info_string
            + f"<p class='info'>page index {quote['page_index']}</p></header>"
            + highlight_spans(quote["page_text"], quote["quote_offsets_page"])
            + "</section>",
        )


    def current_seq2seq_page():
        return display_seq2seq_page(
            quotes_pages.row(quote_slider.value, named=True)
        )
    return (current_seq2seq_page,)


@app.cell(hide_code=True)
def _(pl, quote_annotations):
    # adjust annotation start/end indices to make them relative to the page, then convert to string page span notation
    # then group annotations by page, with page text and list of all page spans for annotated quotes on that page

    # calculate page offsets, then turn into span
    quote_page_spans = (
        quote_annotations.with_columns(
            start_index=pl.col("start_index").sub(pl.col("page_start")),
            end_index=pl.col("end_index").sub(pl.col("page_start")),
        )
        .with_columns(
            page_span=pl.concat_str(
                [pl.col("start_index"), pl.col("end_index")], separator="-"
            )
        )
        .select(
            pl.col("page_index", "page_span", "page_text"),
        )  # limit to just page index and quote span on the page
        .group_by("page_index")  # group by pages
        .all()
    )

    quote_page_spans = quote_page_spans.with_columns(
        page_span=pl.col("page_span").list.join(
            ","
        ),  # combine multiple page spans
        page_text=pl.col("page_text").list.first(),
    )
    return (quote_page_spans,)


@app.cell(hide_code=True)
def _(highlight_spans, mo, pl, quote_page_spans, quote_slider, quotes_pages):
    def display_annotation_page(annotation_page):
        # display an annotation page with page text and aggregated page spans
        text = highlight_spans(
            annotation_page["page_text"], annotation_page["page_span"]
        )

        return mo.Html(f"""<section class='page'><header><h1>annotated quote</h2>
        <p class='info'>page index {annotation_page["page_index"]}</p></header>
        {text}
        </section>""")


    def current_selected_annotation():
        # display the annotation page based on current slider selection
        # get page index from quote pages row
        page_index = quotes_pages.row(quote_slider.value, named=True)["page_index"]
        # get annotation page by page index with text and spans as dict
        annotation_page = quote_page_spans.filter(
            pl.col("page_index").eq(page_index)
        ).row(0, named=True)

        return display_annotation_page(annotation_page)
    return (current_selected_annotation,)


@app.cell(hide_code=True)
def _(pl, quote_page_spans):
    import re
    # generate heuristic search results for the pages in range


    # adapted from find_quotes method in find-quotes notebook
    def find_quotes_spans(text):
        spans = []
        # Find basic quotes of the form „ ... “ or „ ... "
        for match in re.finditer(r"„[^“\"]+[“\"]", text):
            start, end = match.span()
            spans.append(f"{start}-{end}")
        return ",".join(spans)


    heuristic_quote_spans = quote_page_spans.select(
        pl.col("page_index", "page_text")
    ).with_columns(
        heuristic_spans=pl.col("page_text").map_elements(
            find_quotes_spans, return_dtype=pl.String
        )
    )
    return (heuristic_quote_spans,)


@app.cell(hide_code=True)
def _(
    heuristic_quote_spans,
    highlight_spans,
    mo,
    pl,
    quote_slider,
    quotes_pages,
):
    def display_heuristic_quotes_page(annotation_page):
        text = highlight_spans(
            annotation_page["page_text"], annotation_page["heuristic_spans"]
        )

        return mo.Html(f"""<section class='page'><header><h1>identified based on quotation marks</h1>
        <p class='info'>page index {annotation_page["page_index"]}</p></header>
        {text}
        </section>""")


    def current_page_heuristic_quotes():
        # get page index from quote pages row
        page_index = quotes_pages.row(quote_slider.value, named=True)["page_index"]
        # get annotation page by page index with text and spans as dict
        page = heuristic_quote_spans.filter(
            pl.col("page_index").eq(page_index)
        ).row(0, named=True)

        return display_heuristic_quotes_page(page)
    return (current_page_heuristic_quotes,)


@app.cell(hide_code=True)
def _(mo):
    show_annotations = mo.ui.switch(label="annotations", value=True)
    show_seq2seq = mo.ui.switch(label="seq2seq", value=True)
    show_heuristic = mo.ui.switch(label="quotation marks", value=True)
    switch_stack = mo.hstack(
        [show_annotations, show_seq2seq, show_heuristic], justify="start"
    )
    return show_annotations, show_heuristic, show_seq2seq, switch_stack


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Compare quotation methods""")
    return


@app.cell(hide_code=True)
def _(mo, quotes_pages, switch_stack):
    quote_slider = mo.ui.slider(
        start=0,
        stop=quotes_pages.height - 1,
        step=1,
        label="seq2seq quote",
    )

    mo.vstack(
        [
            quote_slider,
            switch_stack,
            mo.md(
                "Use the slider to move through results. Use the toggles to control which panels are shown."
            ),
        ]
    )
    return (quote_slider,)


@app.cell(hide_code=True)
def _(
    current_page_heuristic_quotes,
    current_selected_annotation,
    current_seq2seq_page,
    mo,
    show_annotations,
    show_heuristic,
    show_seq2seq,
):
    panels = []
    # show this one first, since the display is keyed to seq2seq pages
    if show_seq2seq.value:
        panels.append(current_seq2seq_page())
    if show_annotations.value:
        panels.append(current_selected_annotation())
    if show_heuristic.value:
        panels.append(current_page_heuristic_quotes())

    mo.hstack(panels)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ---

    ## seq2seq raw output

    In case it's useful, the table below shows the quotes data as output by seq2seq quotation detection.
    """
    )
    return


@app.cell
def _(mo, quotes_df):
    mo.ui.table(
        quotes_df,
        page_size=15,
        selection=None,
        label="seq2seq quotes data",
    )
    return


if __name__ == "__main__":
    app.run()
