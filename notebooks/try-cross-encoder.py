import marimo

__generated_with = "0.13.11"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import matplotlib.pyplot as plt
    import polars as pl
    import seaborn as sns

    from sentence_transformers import CrossEncoder
    return CrossEncoder, mo, pl, plt, sns


@app.cell
def _(pl):
    # Load in chromadb results since it includes DNZ and Marx sentence text
    all_pairs_df = pl.read_csv("data/sentence-pairs/chromadb-top10.csv")
    all_pairs_df
    return (all_pairs_df,)


@app.cell
def _(all_pairs_df, pl):
    # Reduce to a smaller subset
    working_pairs_df = all_pairs_df.filter(
        (pl.col("is_match")) | (pl.col("distance") <= 0.75)
    )
    working_pairs_df.with_row_index()
    return (working_pairs_df,)


@app.cell
def _(mo):
    mo.md(
        r"""
    The pretrained cross encoder models may not be that well suited to our task.
    They all appear to be trained on the Microsoft Machine Reading Comprehension (MS MARCO)'s passage ranking dataset.
    This effectively trains on question-answer pairs, which is not a great fit for our quotation detection task.
    """
    )
    return


@app.cell
def _(CrossEncoder):
    model = CrossEncoder("cross-encoder/msmarco-MiniLM-L6-en-de-v1")
    return (model,)


@app.cell
def _(model, pl, working_pairs_df):
    # Construct results
    results_df = working_pairs_df.with_columns(
        pl.struct(["dnz_text", "marx_text"])
        .map_elements(
            lambda x: model.predict([(x["dnz_text"], x["marx_text"])]),
            return_dtype=pl.Float64,
        )
        .alias("score")
    )

    results_df
    return (results_df,)


@app.cell
def _(plt, results_df, sns):
    sns.scatterplot(results_df, x="distance", y="score", hue="is_match", alpha=0.7)
    plt.title("Embedding Distance vs. Cross Encoder Score")
    return


@app.cell
def _(mo):
    mo.md(
        r"""As we can see from the above graph, there doesn't appear to be a correlation between the embedding distance and cross encoder scores. So, as suspected, the pretrained cross encoder does not appear to be well-suited for our task."""
    )
    return


if __name__ == "__main__":
    app.run()
