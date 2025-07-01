import marimo

__generated_with = "0.13.11"
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
def _(umap, word_embed):
    # reduce the embeddings with UMAP for plotting
    reducer = umap.UMAP()

    embedding = reducer.fit_transform(word_embed)
    print(word_embed.shape)
    return (embedding,)


@app.cell
def _(embedding, pl, word_meta):
    # convert the embeddings array into a polars dataframe
    embedding_df = pl.from_numpy(embedding, schema=["x", "y"]).with_row_index()

    # join with word metadata
    embedding_df = embedding_df.join(word_meta, left_on="index", right_on="row_id")

    # the field of interest for us is "anno_mentions_kapital", which is a yes/no/maybe field
    # based on annotation data

    embedding_df
    return (embedding_df,)


@app.cell
def _(alt, embedding_df):
    # plot the embeddings with altair
    # combine with a clickable histogram plot by status so tokens can be selected based on annotation status


    click = alt.selection_point(encodings=["color"])

    # define the color domain so we can control order
    color_domain = {"domain": ["Yes", "Maybe", "No"]}

    scatter = (
        alt.Chart(embedding_df, title="Token embeddings for Kapital")
        .mark_point()
        .encode(
            x=alt.X("x", scale=alt.Scale(zero=False), title=""),
            y=alt.Y("y", title=""),
            color=alt.Color(
                "anno_mentions_kapital", title="Annotated as Kapital"
            ).scale(**color_domain),
            # display sentence text in a hover tooltip
            # do we have indices? might be nice to shorten the text and highlight the token in context
            tooltip="text",
            # are there more fields that would be helpful to display? possible to pass a list
        )
        .transform_filter(click)
    )

    hist = (
        alt.Chart(embedding_df)
        .mark_bar()
        .encode(
            x=alt.X("count()", title="Count"),
            y=alt.Color("anno_mentions_kapital", title="").scale(**color_domain),
            color=alt.condition(
                click, "anno_mentions_kapital", alt.value("lightgray")
            ),
        )
        .add_selection(click)
    )

    (scatter & hist).interactive()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    How to interact with this plot:

    - Hover over the circles to see sentence text
    - Click on bars in the histogram plot to filter the scatter plot by category.
    - Zoom in on the upper plot to see a specific area in more detail.
    - Double-click anywhere on the plot to reset.
    """
    )
    return


if __name__ == "__main__":
    app.run()
