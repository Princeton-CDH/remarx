import marimo

__generated_with = "0.14.9"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import polars as pl
    import numpy as np
    import umap
    import altair as alt
    return alt, mo, np, pl, umap


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # Plot token embeddings for Kapital

    We have already generated token-level embeddings for all mentions of "Kapital" in our test data.  

    Let's use UMAP for dimensionality reduction and plot them on a graph to get an initial sense how similar or different the uses of the term are.
    """
    )
    return


@app.cell
def _(np):
    # load pre-computed embeddings
    word_embed = np.load("data/token-embeddings/kapital.npy")
    # confirm expected shape
    word_embed.shape
    return (word_embed,)


@app.cell
def _(pl):
    # load metadata file linking words to their sentences
    word_meta = pl.read_csv("data/token-embeddings/kapital.csv")
    # also load sentences with metadata about mentions
    sentence_df = pl.read_ndjson(
        "data/sentence-corpora/title-mentions-sents.jsonl"
    )
    # join word metadata with sentence data; this gives us information on which sentences are known to mention Kapital
    word_meta = word_meta.join(sentence_df, on="sent_id")

    word_meta
    return (word_meta,)


@app.cell
def _(pl, word_meta):
    # determine which instances of the term have a preceding quote
    from remarx.get_token_embeddings import get_term_spans


    def token_has_preceding_quote(text, token_order):
        spans = get_term_spans(text, "Kapital")
        span = spans[token_order]
        preceding_character = text[span[0] - 1]
        return "Yes" if preceding_character == "„" else "No"


    term_is_quoted = word_meta.select(
        # Create a struct that has two columns in it:
        pl.struct(["text", "token_order"])
        .map_elements(
            lambda combined: token_has_preceding_quote(
                combined["text"], combined["token_order"]
            ),
            return_dtype=pl.datatypes.String,
        )
        .alias("is_quoted")
    )
    # word_meta_quotes = word_meta.map_rows(token_has_preceding_quote)
    word_meta_quotes = word_meta.with_columns(term_is_quoted)
    word_meta_quotes
    return (word_meta_quotes,)


@app.cell
def _(umap, word_embed):
    # reduce the embeddings with UMAP for plotting
    reducer = umap.UMAP()

    embedding = reducer.fit_transform(word_embed)
    print(word_embed.shape)
    return (embedding,)


@app.cell
def _(embedding, pl, word_meta_quotes):
    # convert the embeddings array into a polars dataframe
    embedding_df = pl.from_numpy(embedding, schema=["x", "y"]).with_row_index()

    # join with word metadata
    embedding_df = embedding_df.join(
        word_meta_quotes, left_on="index", right_on="row_id"
    )

    # the field of interest for us is "anno_mentions_kapital", which is a yes/no/maybe field
    # based on annotation data

    embedding_df
    return (embedding_df,)


@app.cell
def _(alt, embedding_df):
    # plot the embeddings with altair
    # combine with a clickable histogram plot by status so tokens can be selected based on annotation status


    select_color = alt.selection_point(fields=["anno_mentions_kapital"])
    select_shape = alt.selection_point(fields=["is_quoted"])

    # define the color domain so we can control order
    color_domain = {"domain": ["Yes", "Maybe", "No"]}
    # samef or shape, so it doesn't change when filtering
    shape_domain = {"domain": ["Yes", "No"], "range": ["triangle", "circle"]}

    scatter = (
        alt.Chart(embedding_df, title="Token embeddings for Kapital")
        .mark_point()
        .encode(
            x=alt.X("x", scale=alt.Scale(zero=False), title=""),
            y=alt.Y("y", title=""),
            # olor=alt.condition(selection_first_name & selection_last_name,
            #                 alt.Color('First name:N', legend=None),
            #                 alt.value('lightgray') ),
            # color=alt.Color(
            # "anno_mentions_kapital", title="Annotated as Kapital"
            # ).scale(**color_domain),
            color=alt.condition(
                select_color,
                alt.Color("anno_mentions_kapital:N", title="Title Mention").scale(
                    **color_domain
                ),
                alt.value("lightgray"),
            ),
            shape=alt.Shape("is_quoted").scale(**shape_domain),
            # display sentence text in a hover tooltip
            # do we have indices? might be nice to shorten the text and highlight the token in context
            tooltip=["text"],
            # are there more fields that would be helpful to display? possible to pass a list
        )
        .transform_filter(select_color & select_shape)
        # .transform_filter(select_shape)
    )

    hist = (
        alt.Chart(embedding_df)
        .mark_bar()
        .encode(
            x=alt.X("count()", title=""),
            y=alt.Y("anno_mentions_kapital", title="").scale(**color_domain),
            color=alt.condition(
                select_color, "anno_mentions_kapital", alt.value("lightgray")
            ),
        )
        .add_selection(select_color)
    )
    quoted_hist = (
        alt.Chart(embedding_df)
        .mark_bar()
        .encode(
            x=alt.X("count()", title="Total"),
            y=alt.Y("is_quoted", title="Quoted").scale(domain=["Yes", "No"]),
            color=alt.condition(select_shape, "is_quoted", alt.value("lightgray")),
        )
        .add_selection(select_shape)
    )

    (scatter & hist & quoted_hist).interactive()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    How to interact with this plot:

    - Hover over the circles to see sentence text
    - Click on bars in either of the the histogram plot to filter the scatter plot by category (annotation title status, or whether the term is quoted).
    - Zoom in on the upper plot to see a specific area in more detail.
    - Double-click anywhere on the plot to reset.
    """
    )
    return


@app.cell
def _(mo):
    mo.md(
        r"""
    ### Insights


    - Good news: there's clear separation between two different clusters of tokens!
    - Bad news: the clusters we see seem to be primarily based on the presence of quotes... 😞

    Per Laure, the tokenization is different depending on the quotations, since the terms of interest may get broken into subtokens differently - and the average of those combined subtokens will be more like each other and different from other terms that are tokenized differently, which is what we see.

    If we had more time for this experiment, we would strip out quotes around single terms and short phrases first before generating the token embeddings and see how that impacts our results.
    """
    )
    return


if __name__ == "__main__":
    app.run()
