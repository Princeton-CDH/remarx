import marimo

__generated_with = "0.12.10"
app = marimo.App(width="medium", css_file="custom.css")


@app.cell
def _():
    import marimo as mo
    import polars as pl
    return mo, pl


@app.cell
def _(pl):
    # load test subset data
    quote_subset_pages = pl.read_csv("data/subset/direct_quotes.csv")
    quote_subset_pages
    return (quote_subset_pages,)


@app.cell(hide_code=True)
def _(mo, quote_subset_pages):
    quote_slider = mo.ui.slider(
        start=0,
        stop=quote_subset_pages.height - 1,
        step=1,
        label="Quote",
    )

    mo.vstack(
        [
            quote_slider,
            mo.md("Move the slider to change which quote is displayed."),
        ]
    )
    return (quote_slider,)


@app.cell(hide_code=True)
def _(mo, quote_slider, quote_subset_pages):
    def show_page_html(quote):
        page_start_index, page_end_index = (
            quote["start_index"] - quote["page_start"],
            quote["end_index"] - quote["page_start"],
        )
        before_quote = quote["page_text"][0:page_start_index]
        quote_text = quote["page_text"][page_start_index:page_end_index]
        after_quote = quote["page_text"][page_end_index:]

        return mo.Html(f"""
        <p>Page index: {quote["page_index"]} (article: {page_start_index}:{page_end_index} page: {page_start_index}:{page_end_index})</p>

        <div class='span-compare'>
        <div>{before_quote}<span class='hi'>{quote_text}</span>{after_quote}</div>
        </div>
        """)


    show_page_html(quote_subset_pages.row(quote_slider.value, named=True))
    return (show_page_html,)


@app.cell
def _(mo, quote_slider, quote_subset_pages):
    def highlight_span(text, start, end):
        before = text[:start]
        span = text[start:end]
        after = text[end:]
        return f"<div>{before}<span class='hi'>{span}</span>{after}</div>"


    def test_show_multiple(quote):
        # make char offset relative to page start for indexing within page text
        page_start_index, page_end_index = (
            quote["start_index"] - quote["page_start"],
            quote["end_index"] - quote["page_start"],
        )
        highlight_annotation = highlight_span(
            quote["page_text"], page_start_index, page_end_index
        )

        # TEMPORARY: for testing purposes just select some arbitrary text that overlaps with the real span
        span_start = page_start_index - 15
        span_end = page_start_index + 22
        second_anno = highlight_span(quote["page_text"], span_start, span_end)

        return mo.Html(f"""
        <p>Page index: {quote["page_index"]} (article: {page_start_index}:{page_end_index} page: {page_start_index}:{page_end_index})</p>

        <div class='span-compare'>
        {highlight_annotation}
        {second_anno}
        </div>
        """)


    test_show_multiple(quote_subset_pages.row(quote_slider.value, named=True))
    return highlight_span, test_show_multiple


if __name__ == "__main__":
    app.run()
