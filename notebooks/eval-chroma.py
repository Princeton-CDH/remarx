import marimo

__generated_with = "0.13.11"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import matplotlib.pyplot as plt
    import polars as pl
    import seaborn as sns

    from remarx.eval_knn import (
        precision_at_distance,
        recall_at_distance,
        recall_at_k,
    )
    return (
        mo,
        np,
        pl,
        plt,
        precision_at_distance,
        recall_at_distance,
        recall_at_k,
        sns,
    )


@app.cell
def _(mo):
    mo.md(r"""# Evaluating ChromaDB Results""")
    return


@app.cell
def _(mo):
    mo.md(r"""## Load Data""")
    return


@app.cell
def _(pl):
    # Load in the sentence pair results for ChromaDB for 10-nearest neighbors
    all_pairs_df = pl.read_csv("data/sentence-pairs/chromadb-top10.csv")
    all_pairs_df
    return (all_pairs_df,)


@app.cell
def _(all_pairs_df, pl):
    # Filter to known matching pairs (i.e., true positives)
    true_pairs_df = all_pairs_df.filter(pl.col("is_match"))
    true_pairs_df
    return


@app.cell
def _(mo):
    mo.md(
        r"""
    ## Recall@k
    First, we'll see how many nearest neighbors it takes to find our test set of DNZ-Marx sentence pairs.
    """
    )
    return


@app.cell
def _(all_pairs_df, pl, plt, recall_at_k, sns):
    max_rank = all_pairs_df.get_column("rank").max()
    rank_recall_results = []
    for i in range(1, max_rank + 2):
        rank_recall_results.append(
            {"rank": i, "rank@k": recall_at_k(all_pairs_df, i)}
        )

    sns.pointplot(data=pl.DataFrame(rank_recall_results), x="rank", y="rank@k")
    plt.xlabel("Rank")
    plt.ylabel("Recall")
    plt.title("Recall@k")
    return


@app.cell
def _(mo):
    mo.md(
        rf"""As we can see, the majority of matching DNZ-Marx sentence pairs are the first nearest neighbor. However, we need the top five nearest neighbors in order to retrieve all matching pairs."""
    )
    return


@app.cell
def _(mo):
    mo.md(
        r"""
    ## Examining Sentence Distances
    We'll try a few visualizations to get a sense of the distance values for all retrieved DNZ-Marx sentences pairs, both correct and incorrect matches.
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
    ax_strip.set_xticks(np.arange(0, 1.9, 0.1))
    for dist1 in true_dists:
        ax_strip.axvline(x=dist1, color="orange", linestyle="--")
    ax_strip.set_title("DNZ-Marx Distances\n(true matches in orange)")
    plt.show()
    return


@app.cell
def _(mo):
    mo.md(
        r"""In good news, the smallest distances correspond exclusively to matching sentence pairs. However, two of the matching pairs have distances higher than many incorrect sentence pairs."""
    )
    return


@app.cell
def _(mo):
    mo.md(r"""## Evaluating Distance Thresholds""")
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

    for d in np.arange(0.1, 0.95, 0.05):
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
    mo.md(
        r"""
    By examining the precision and recall scores for different distance thresholds we can see the trade-offs between for different values. From this we can see we get the best precision (the proportion of retrieved sentence pairs that are correct matches) when we have a distance threshold at or below a distance of 0.4. In contrast, we get the best recall (i.e., all correct matches are retrieved) when we have a distance threshold at or above 0.8.

    We'll want a threshold in between this that strikes a balance between precision and recall, since we want to identify correct matches but without too many false positives. We can use the $F_1$ score

    $$F_1 = 2\frac{\text{precision}*\text{recall}}{\text{precision}+\text{recall}}$$

    to help determine a good starting threshold. We observe the highest $F_1$ score when we set our distance threshold to 0.45. For this threshold, seven sentence pairs will be retrieved with six of them corresponding to matching sentence pairs and only one bad match.
    """
    )
    return


if __name__ == "__main__":
    app.run()
