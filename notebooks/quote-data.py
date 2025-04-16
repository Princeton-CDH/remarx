import marimo

__generated_with = "0.12.9"
app = marimo.App(width="medium", auto_download=["ipynb"])


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        # Identify subset of examples for direct quotes

        ## Load & filter annotation data

        **Goal:** Find a subset of pages with direct quotes to be use for testing and experimentation.
        """
    )
    return


@app.cell
def _():
    import marimo as mo
    import polars as pl
    return mo, pl


@app.cell
def _(pl):
    # load all annotation data files
    df = pl.read_csv("data/annotation/*.csv")
    # limit to the columns we care about
    df = df.select(
        pl.col("UUID", "FILE", "QUOTE_TRANSCRIPTION", "ANCHOR", "TAGS", "COMMENTS")
    )
    # turn char-offset into numeric start index, calculate end index
    df = (
        df.with_columns(start_index=pl.col("ANCHOR").str.slice(12).cast(dtype=int))
        .with_columns(
            end_index=pl.col("start_index").add(
                pl.col("QUOTE_TRANSCRIPTION").str.len_chars()
            )
        )
        .drop("ANCHOR")
    )
    df
    return (df,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""Filter to the subset of annotations that have direct references to the texts that are in scope for this phase.""")
    return


@app.cell
def _(df, pl):
    # filter to the subset with direct quotes from texts of interest
    # - we want tag only, no qualification such as |Title Reference or |Concept Reference
    quotes_df = df.filter(
        pl.col("TAGS").is_in(["Kapital", "Manifest der Kommunistischen Partei"])
    )
    quotes_df
    return (quotes_df,)


@app.cell
def _(pl, quotes_df):
    quotes_df.group_by("FILE").agg(
        pl.col("TAGS").count().alias("count"),
        pl.col("TAGS").unique().str.join("|"),
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""`1896-97aCLEAN.txt` has the most direct quotes and has some from both Marx texts; let's use that one.""")
    return


@app.cell
def _(pl, quotes_df):
    # 1896-97aCLEAN.txt has the most direct quotes and has some from both texts
    quote_subset_df = quotes_df.filter(pl.col("FILE").eq("1896-97aCLEAN.txt"))
    quote_subset_df
    return (quote_subset_df,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ## Load article text and chunk roughly into pages

        Load the text contents of the file for the annotations we want to use and make sure we can match pages of text to the annotated text.
        """
    )
    return


@app.cell
def _(pl):
    # load text file and chunk into pages

    with open("data/text/1896-97aCLEAN.txt") as inputfile:
        text = inputfile.read()
        pages = text.split("\n\n\n")

    page_df = pl.DataFrame(data={"text": pages}).with_row_index()
    # add field to calculate text length
    page_df = page_df.with_columns(text_length=pl.col("text").str.len_chars())
    page_df
    return inputfile, page_df, pages, text


@app.cell
def _(page_df):
    # calculate start index for each page based on preceding text length + split characters
    page_start_indices = []
    # first page index is zero
    current_index = 0
    for page in page_df.iter_rows(named=True):
        # add current page index to the list
        page_start_indices.append(current_index)
        # add length of this place plus characters used to split
        current_index += page["text_length"] + 3
    return current_index, page, page_start_indices


@app.cell
def _(page_df, page_start_indices, pl):
    # add page start index to the dataframe of page text and calculate end of page
    page_df_start = page_df.insert_column(
        3, pl.Series("page_start", page_start_indices)
    ).with_columns(page_end=pl.col("page_start").add(pl.col("text_length")))
    page_df_start
    return (page_df_start,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""Spot check alignment of page text and annotation text.""")
    return


@app.cell
def _(quotes_df):
    # check text index matching
    first_row = quotes_df.row(0, named=True)
    first_row
    return (first_row,)


@app.cell
def _(first_row, text):
    text_substring = text[first_row["start_index"] : first_row["end_index"]]
    print(text_substring)
    return (text_substring,)


@app.cell
def _(first_row):
    print(first_row["QUOTE_TRANSCRIPTION"])
    return


@app.cell
def _(first_row, text_substring):
    text_substring.replace("\n", " ") == first_row["QUOTE_TRANSCRIPTION"]
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        The text in the exported annotation does not include newlines, but once we're calculating text length and start/end index
        correctly, we do have matching text (other than newlines).
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Combine page text with selected annotations""")
    return


@app.cell
def _(page_df_start, pl, quote_subset_df):
    # join subset of quotes with page text; rename page text columns for clarity
    quote_subset_pages = quote_subset_df.join_where(
        page_df_start.rename({"text": "page_text", "index": "page_index"}),
        pl.col("start_index") >= pl.col("page_start"),
        pl.col("start_index") <= pl.col("page_end"),
    )
    quote_subset_pages
    return (quote_subset_pages,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""Check alignment of text between quotes and page text.""")
    return


@app.cell
def _(quote_subset_pages):
    # iterate over quotes and output to check that we're getting the correct content

    for quote in quote_subset_pages.iter_rows(named=True):
        print(quote["QUOTE_TRANSCRIPTION"])
        page_start_index, page_end_index = (
            quote["start_index"] - quote["page_start"],
            quote["end_index"] - quote["page_start"],
        )
        print(f"{quote['TAGS']} (article {quote['start_index']}:{quote['end_index']} / page {page_start_index}:{page_end_index}) ")
        if page_end_index > len(quote['page_text']):
            print("*** quote end index is larger than page content")
        print(quote["page_text"][page_start_index:page_end_index])
        print("\n")
    return page_end_index, page_start_index, quote


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""Some pages have more than one quote, but in this set the quotes on the same page are from the same Marx text.""")
    return


@app.cell
def _(pl, quote_subset_pages):
    # which pages have more than one quote?
    quote_subset_pages.group_by("page_index").agg(
        pl.col("TAGS").count().alias("count"),
        pl.col("TAGS").unique().str.join("|"),
    ).filter(pl.col("count").gt(1))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""See the quotes in the context of the page. Use the slider to move between different quotes.""")
    return


@app.cell(hide_code=True)
def _(mo, quote_subset_pages):
    quote_slider = mo.ui.slider(
        start=0,
        stop=quote_subset_pages.height - 1,
        step=1,
        label="Quote from subset",
    )
    quote_slider
    return (quote_slider,)


@app.cell
def _(mo, quote_slider, quote_subset_pages):
    def show_page(quote):
        page_start_index, page_end_index = (
            quote["start_index"] - quote["page_start"],
            quote["end_index"] - quote["page_start"],
        )
        # at least one page includes an asterisk; escape so we don't get unintentional italics
        before_quote = quote["page_text"][0:page_start_index].replace("*", r"\*")
        quote_text = quote["page_text"][page_start_index:page_end_index].replace(
            "*", r"\*"
        )
        after_quote = quote["page_text"][page_end_index:].replace("*", r"\*")

        return mo.md(f"""
        Tag: {quote["TAGS"]}<br/>
        Page index: {quote["page_index"]} (article: {page_start_index}:{page_end_index} page: {page_start_index}:{page_end_index})

        {before_quote}**{quote_text}**{after_quote}
        """)


    show_page(quote_subset_pages.row(quote_slider.value, named=True))
    return (show_page,)


@app.cell
def _(mo):
    mo.md(r"""Save the identified subset of quotes and associated page text for use in other experiments.""")
    return


@app.cell
def _(quote_subset_pages):
    quote_subset_pages
    return


@app.cell
def _(quote_subset_pages):
    quote_subset_pages.write_csv("data/subset/direct_quotes.csv", include_bom=True)
    return


if __name__ == "__main__":
    app.run()
