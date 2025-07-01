import marimo

__generated_with = "0.13.11"
app = marimo.App(width="medium")


@app.cell
def _():
    # letting this import exist in its own cell to reduce linter warnings
    import marimo as mo
    return (mo,)


@app.cell
def _():
    import pathlib

    import numpy as np
    import polars as pl
    import matplotlib.pyplot as plt
    import seaborn as sns

    from annoy import AnnoyIndex
    from remarx.eval_knn import (
        precision_at_distance,
        recall_at_distance,
        recall_at_k,
    )
    return (
        AnnoyIndex,
        np,
        pathlib,
        pl,
        plt,
        precision_at_distance,
        recall_at_distance,
        recall_at_k,
        sns,
    )


@app.cell
def _(mo):
    mo.md(
        r"""
    # Test using Annoy to find similar sentences
    In this notebook we will will find the the top 10 nearest MEGA sentences for each DNZ sentence.
    In other words, the MEGA sentences will form the index and the DNZ sentences will be queries.
    """
    )
    return


@app.cell
def _(np, pl):
    # Load sentence corpora and embeddings
    ## Load sentence corpora
    dnz_sents_df = (
        pl.scan_ndjson("data/sentence-corpora/dnz-sample-sents.jsonl")
        .select(["sent_id", "text"])
        .with_row_index()
        .rename(lambda x: f"dnz_{x}")
        .collect()
    )
    marx_sents_df = (
        pl.scan_ndjson("data/sentence-corpora/mega-sample-sents.jsonl")
        .select(["sent_id", "text"])
        .with_row_index()
        .rename(lambda x: f"marx_{x}")
        .collect()
    )

    ## Load embeddings
    marx_embeddings = np.load("data/sentence-embeddings/mega-sample-sents.npy")
    dnz_embeddings = np.load("data/sentence-embeddings/dnz-sample-sents.npy")
    return dnz_embeddings, dnz_sents_df, marx_embeddings, marx_sents_df


@app.cell
def _(mo):
    mo.md(r"""## Run Annoy""")
    return


@app.cell
def _(mo):
    mo.md(
        r"""
    For our Annoy index, we will use the dot product as our distance measurement (note that it really is a similarity measurement and is treated as such by Annoy).
    In our case is the same as cosine similarity since our embeddings are L2 normalized.

    An Annoy index takes one hyperparameter which specifies the number of trees the index will construct. More trees means better precision, but requires more resources.
    For now, we will arbitrarily use 10 trees.

    It's worth noting that we can save the constructed Annoy index over MARX sentences to disk and reload it later to compare to any additional sentence embeddings we might have later on.
    This could be a possible advantage over other methods.
    """
    )
    return


@app.cell
def _(AnnoyIndex, marx_embeddings):
    # Build annoy index for Marx sentence embeddings
    n_features = marx_embeddings.shape[1]

    # Instantiate annoy index, use dot product
    marx_index = AnnoyIndex(n_features, "dot")

    # Add each embedding to index
    for i, row in enumerate(marx_embeddings):
        marx_index.add_item(i, row)

    # Build index with 10 trees, for now not saving (will do this if building the index is too slow)
    _ = marx_index.build(10)
    return (marx_index,)


@app.cell
def _(dnz_embeddings, dnz_sents_df, marx_index, marx_sents_df, pl):
    # Build knn results
    entries = []
    for dnz_i, dnz_vec in enumerate(dnz_embeddings):
        knn_results = marx_index.get_nns_by_vector(
            dnz_vec, n=10, include_distances=True
        )
        for rank in range(10):
            # Marx sentence row index
            marx_i = knn_results[0][rank]

            # Since our embeddings are L2 normalized, dot product is equivalent to cosine simularity
            # For consistency, convertint to cosine distance (1 - cos_sim(x,y)) which has a range of 0 to 2
            dist = 1 - knn_results[1][rank]
            entries.append(
                {
                    "dnz_index": dnz_i,
                    "marx_index": marx_i,
                    "rank": rank,
                    "distance": dist,
                }
            )

    results_df = (
        pl.DataFrame(entries)
        .join(dnz_sents_df, on="dnz_index")
        .join(marx_sents_df, on="marx_index")
    )
    results_df
    return (results_df,)


@app.cell
def _(pl):
    # Load the evaulation data and filter to those that have sentence ids for both sentence corpora
    eval_pairs_df = pl.read_csv(
        "data/sentence-eval-pairs/dnz_marx_sentence_pairs.csv"
    )
    eval_pairs_df = eval_pairs_df.filter(
        pl.col("marx_sent_id").is_not_null(), pl.col("dnz_sent_id").is_not_null()
    )
    eval_pairs_df
    return (eval_pairs_df,)


@app.cell
def _(eval_pairs_df, pathlib, pl, results_df):
    # Add sentence-pair match information to results before saving
    match_indices = (
        results_df.with_row_index()
        .join(eval_pairs_df, on=["dnz_sent_id", "marx_sent_id"])
        .get_column("index")
        .implode()
    )


    output_df = (
        results_df.with_row_index()
        .with_columns(pl.col("index").is_in(match_indices).alias("is_match"))
        .select(
            [
                "dnz_sent_id",
                "marx_sent_id",
                "distance",
                "rank",
                "is_match",
                "dnz_text",
                "marx_text",
            ]
        )
    )

    # Only save to file if it doesn't exist
    output_csv = pathlib.Path("data/sentence-pairs/annoy10-top10.csv")
    if not output_csv.is_file():
        output_df.write_csv("data/sentence-pairs/annoy10-top10.csv")
    return (output_df,)


@app.cell
def _(mo):
    mo.md(r"""## Evaluate Annoy Results""")
    return


@app.cell
def _(output_df, pl):
    all_pairs_df = output_df

    # Filter to known matching pairs (i.e., true positives)
    true_pairs_df = all_pairs_df.filter(pl.col("is_match"))
    true_pairs_df
    return (all_pairs_df,)


@app.cell
def _(mo):
    mo.md(r"""### Recall@k""")
    return


@app.cell
def _(mo):
    mo.md(
        r"""When we take a look at recall, we find that annoy performs as well as ChromaDB for a our sample set."""
    )
    return


@app.cell
def _(all_pairs_df, pl, plt, recall_at_k, sns):
    max_rank = all_pairs_df.get_column("rank").max()
    rank_recall_results = []
    for rank_i in range(1, max_rank + 2):
        rank_recall_results.append(
            {"rank": rank_i, "rank@k": recall_at_k(all_pairs_df, rank_i)}
        )

    sns.pointplot(data=pl.DataFrame(rank_recall_results), x="rank", y="rank@k")
    plt.xlabel("Rank")
    plt.ylabel("Recall")
    plt.title("Recall@k")
    return


@app.cell
def _(mo):
    mo.md(r"""### Examining Sentence Distances""")
    return


@app.cell
def _(mo):
    mo.md(
        r"""
    Perhaps unsurprisingly, we observe no real difference between ChromaDB and Annoy in the distribution across the distances of DNZ sentences and their top 10 nearest MARX sentences.
    Given the small-scale we're operating in, there may not be much of a difference until we operate at much larger scales.

    Note that the absolute range of distances is different between ChromaDB and Annoy, but that's simply due to the different distance measure being used.
    """
    )
    return


@app.cell
def _(all_pairs_df, pl):
    # For drawing figures
    true_dists = (
        all_pairs_df.filter(pl.col("is_match")).get_column("distance").to_list()
    )
    return (true_dists,)


@app.cell
def _(all_pairs_df, plt, sns, true_dists):
    ax_dists = sns.histplot(all_pairs_df, x="distance", stat="count")
    # Add vertical lines to mark matches
    for dist2 in true_dists:
        ax_dists.axvline(x=dist2, color="orange", linestyle="--")
    plt.title("DNZ-Marx Distances\n(orange lines indicate true matches)")
    plt.show()
    return


@app.cell
def _(all_pairs_df, np, plt, sns, true_dists):
    plt.figure(figsize=(10, 3))
    ax_strip = sns.stripplot(
        all_pairs_df,
        x="distance",
        hue="is_match",
        jitter=0.25,
        alpha=0.6,
        legend=False,
    )
    ax_strip.set_xticks(np.arange(0, 1.0, 0.1))
    for dist1 in true_dists:
        ax_strip.axvline(x=dist1, color="orange", linestyle="--")
    ax_strip.set_title("DNZ-Marx Distances\n(true matches in orange)")
    plt.show()
    return


@app.cell
def _(mo):
    mo.md(r"""### Evaluating Distance Thresholds""")
    return


@app.cell
def _(mo):
    mo.md(
        r"""For cosine distance, we observe that a threshold near 0.225 results in the best F1 score."""
    )
    return


@app.cell
def _(
    all_pairs_df,
    np,
    pl,
    plt,
    precision_at_distance,
    recall_at_distance,
    sns,
    true_dists,
):
    plt.figure(figsize=(10, 3))
    dist_results = []

    for d in np.arange(0.1, 0.55, 0.025):
        precision_score = precision_at_distance(all_pairs_df, d)
        recall_score = recall_at_distance(all_pairs_df, d)
        # Add precision score
        dist_results.append(
            {
                "distance": d,
                "score": precision_score,
                "measure": "Precision",
            }
        )
        # Add recall score
        dist_results.append(
            {
                "distance": d,
                "score": recall_score,
                "measure": "Recall",
            }
        )
        # Add F1 score
        dist_results.append(
            {
                "distance": d,
                "score": 2
                * (precision_score * recall_score)
                / (precision_score + recall_score),
                "measure": "F1",
            }
        )

    ax_points = sns.pointplot(
        pl.DataFrame(dist_results),
        x="distance",
        y="score",
        hue="measure",
        native_scale=True,
    )
    ax_points.axvline(x=max(true_dists), linestyle=":", color="black")
    plt.text(max(true_dists) + 0.01, 0.5, "max dist for\n   matches")
    plt.title("Precision and Recall for Distance Thresholds")
    sns.move_legend(ax_points, "upper left", bbox_to_anchor=(1, 1))

    plt.show()
    return


@app.cell
def _(mo):
    mo.md(r"""## Takeaways""")
    return


@app.cell
def _(mo):
    mo.md(
        r"""
    Overall, we observe little difference in results between ChromaDB and Annoy.
    This is not particularly surprising given the small scale we are currently operating in.
    We will likely see more substantial differences when trying different models to create our embeddings (and possibly also with different post-processing steps).

    That said, it may be worth switching to cosine distance (or dot product / cosine similarity), so that our distance (or similarity) scores have consistent bounded range.
    In general, we should observe our sentence embeddings to have a cosine similarity between 0 and 1.
    While it is technically possible for cosine similarity to be negative, this seems unlikely to be the case, especially for the nearest distances.
    Granted, this is extrapolating for the geometries of older embeddings spaces which showed that the embeddings in these spaces tend to be quite concentrated as opposed to be more uniformly spread out across the k-dimensional space.
    """
    )
    return


if __name__ == "__main__":
    app.run()
