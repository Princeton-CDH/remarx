"""Generate embedding visualizations for the remarx presentation — Marimo notebook."""

import marimo

__generated_with = "0.10.0"
app = marimo.App()


@app.cell
def _():
    import textwrap

    import matplotlib.patches as mpatches
    import matplotlib.pyplot as plt
    import numpy as np
    import polars as pl
    from sentence_transformers import SentenceTransformer
    from sklearn.manifold import TSNE

    return TSNE, SentenceTransformer, mpatches, np, pl, plt, textwrap


@app.cell
def _():
    # -- paths ------------------------------------------------------------------
    QUOTES_CSV = "/Users/ht8933/remarx-data/quotes/quote_pairs_6_originals_1896-97a XML Output-835pages.csv"
    REUSE_CSV = (
        "/Users/ht8933/remarx-data/corpora/reuse/1896-97a XML Output-835pages.csv"
    )
    ORIG_CSV = (
        "/Users/ht8933/remarx-data/corpora/original/Das_Kapital_MEGA_A2_B005-00_ETX.csv"
    )
    OUT_DIR = "/Users/ht8933/Documents/Documents-cdh-m5945fhwr7/dev/remarx"
    MODEL_NAME = "paraphrase-multilingual-mpnet-base-v2"

    # -- colour palette ---------------------------------------------------------
    C_ORIG = "#2166ac"  # blue  - Das Kapital
    C_REUSE = "#d6604d"  # red   - DNZ articles
    C_MATCH = "#4dac26"  # green - match connector
    return (
        C_MATCH,
        C_ORIG,
        C_REUSE,
        MODEL_NAME,
        ORIG_CSV,
        OUT_DIR,
        QUOTES_CSV,
        REUSE_CSV,
    )


@app.cell
def _(SentenceTransformer, np):
    def embed(texts: list[str], model: SentenceTransformer) -> np.ndarray:
        """Encode texts into normalised embeddings."""
        return model.encode(texts, normalize_embeddings=True, show_progress_bar=False)

    return (embed,)


@app.cell
def _(MODEL_NAME, ORIG_CSV, QUOTES_CSV, REUSE_CSV, SentenceTransformer, pl):
    def load_data() -> tuple:
        """Load quotes + corpus text, return joined DataFrames and model."""
        quotes = pl.read_csv(QUOTES_CSV, infer_schema_length=10000)
        reuse_df = pl.read_csv(REUSE_CSV, infer_schema_length=0)
        orig_df = pl.read_csv(ORIG_CSV, infer_schema_length=0)
        model = SentenceTransformer(MODEL_NAME)
        return quotes, reuse_df, orig_df, model

    return (load_data,)


@app.cell
def _(
    C_MATCH,
    C_ORIG,
    C_REUSE,
    OUT_DIR,
    TSNE,
    SentenceTransformer,
    embed,
    mpatches,
    np,
    pl,
    plt,
):
    def fig1_matched_pairs(
        quotes: pl.DataFrame,
        reuse_df: pl.DataFrame,
        orig_df: pl.DataFrame,
        model: SentenceTransformer,
    ) -> None:
        """Plot matched pairs in 2-D t-SNE space, connected by lines."""
        print("Building Figure 1 - matched pairs ...")

        N_PAIRS = 15
        N_BG = 25  # background sentences per corpus

        best = (
            quotes.filter(pl.col("reuse_text").str.len_chars() > 40)
            .filter(pl.col("original_text").str.len_chars() > 40)
            .sort("match_score", descending=True)
            .head(N_PAIRS)
        )
        matched_reuse_ids = set(best["reuse_id"].to_list())
        matched_orig_ids = set(best["original_id"].to_list())

        # background: random sentences not in matched set
        bg_reuse = reuse_df.filter(~pl.col("sent_id").is_in(matched_reuse_ids)).sample(
            N_BG, seed=42
        )
        bg_orig = orig_df.filter(~pl.col("sent_id").is_in(matched_orig_ids)).sample(
            N_BG, seed=42
        )

        # collect all texts in order
        matched_r_texts = best["reuse_text"].to_list()
        matched_o_texts = best["original_text"].to_list()
        bg_r_texts = bg_reuse["text"].to_list()
        bg_o_texts = bg_orig["text"].to_list()

        all_texts = matched_r_texts + matched_o_texts + bg_r_texts + bg_o_texts
        vecs = embed(all_texts, model)

        tsne = TSNE(n_components=2, perplexity=12, random_state=42, max_iter=2000)
        coords = tsne.fit_transform(vecs)

        mr_xy = coords[:N_PAIRS]
        mo_xy = coords[N_PAIRS : 2 * N_PAIRS]
        br_xy = coords[2 * N_PAIRS : 2 * N_PAIRS + N_BG]
        bo_xy = coords[2 * N_PAIRS + N_BG :]

        fig, ax = plt.subplots(figsize=(10, 8))
        fig.patch.set_facecolor("#f8f8f8")
        ax.set_facecolor("#f8f8f8")

        ax.scatter(br_xy[:, 0], br_xy[:, 1], c=C_REUSE, alpha=0.2, s=55, zorder=2)
        ax.scatter(bo_xy[:, 0], bo_xy[:, 1], c=C_ORIG, alpha=0.2, s=55, zorder=2)

        for i in range(N_PAIRS):
            ax.plot(
                [mr_xy[i, 0], mo_xy[i, 0]],
                [mr_xy[i, 1], mo_xy[i, 1]],
                color=C_MATCH,
                lw=1.2,
                alpha=0.55,
                zorder=3,
            )

        ax.scatter(
            mr_xy[:, 0],
            mr_xy[:, 1],
            c=C_REUSE,
            s=100,
            zorder=4,
            edgecolors="white",
            linewidths=0.8,
        )
        ax.scatter(
            mo_xy[:, 0],
            mo_xy[:, 1],
            c=C_ORIG,
            s=100,
            zorder=4,
            edgecolors="white",
            linewidths=0.8,
        )

        # label the 4 best pairs
        for i in range(4):
            short_r = matched_r_texts[i][:45].replace("\n", " ") + "…"
            short_o = matched_o_texts[i][:45].replace("\n", " ") + "…"
            ax.annotate(
                short_r,
                mr_xy[i],
                fontsize=6.5,
                color=C_REUSE,
                xytext=(6, 4),
                textcoords="offset points",
            )
            ax.annotate(
                short_o,
                mo_xy[i],
                fontsize=6.5,
                color=C_ORIG,
                xytext=(6, -10),
                textcoords="offset points",
            )

        ax.legend(
            handles=[
                mpatches.Patch(color=C_REUSE, label="DNZ article sentence (reuse)"),
                mpatches.Patch(color=C_ORIG, label="Das Kapital sentence (original)"),
                plt.Line2D(
                    [0], [0], color=C_MATCH, lw=1.5, label="Detected quotation match"
                ),
            ],
            loc="lower right",
            fontsize=9,
            framealpha=0.9,
            edgecolor="#cccccc",
        )

        ax.set_title(
            "Sentence embeddings in 2-D (t-SNE)\nMatched quotation pairs are connected",
            fontsize=13,
            pad=12,
        )
        ax.set_xlabel("t-SNE dimension 1", fontsize=10)
        ax.set_ylabel("t-SNE dimension 2", fontsize=10)
        ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
        for spine in ax.spines.values():
            spine.set_visible(False)

        out = f"{OUT_DIR}/fig1_matched_pairs.png"
        fig.savefig(out, dpi=180, bbox_inches="tight")
        plt.close(fig)
        print(f"  saved -> {out}")

    return (fig1_matched_pairs,)


@app.cell
def _(
    C_MATCH,
    C_ORIG,
    C_REUSE,
    OUT_DIR,
    TSNE,
    SentenceTransformer,
    embed,
    mpatches,
    pl,
    plt,
):
    def fig2_semantic_clusters(
        quotes: pl.DataFrame,
        reuse_df: pl.DataFrame,
        orig_df: pl.DataFrame,
        model: SentenceTransformer,
    ) -> None:
        """Plot both corpora in the same t-SNE space, highlighting matched sentences."""
        print("Building Figure 2 - semantic clusters ...")

        N = 120
        matched_reuse_ids = set(quotes["reuse_id"].to_list())
        matched_orig_ids = set(quotes["original_id"].to_list())

        sample_r = reuse_df.sample(N, seed=7)
        sample_o = orig_df.sample(N, seed=7)

        r_texts = sample_r["text"].to_list()
        o_texts = sample_o["text"].to_list()
        r_ids = sample_r["sent_id"].to_list()
        o_ids = sample_o["sent_id"].to_list()

        vecs = embed(r_texts + o_texts, model)
        tsne = TSNE(n_components=2, perplexity=25, random_state=0, max_iter=2000)
        coords = tsne.fit_transform(vecs)

        fig, ax = plt.subplots(figsize=(10, 8))
        fig.patch.set_facecolor("#f8f8f8")
        ax.set_facecolor("#f8f8f8")

        for i in range(N):
            matched = r_ids[i] in matched_reuse_ids
            ax.scatter(
                coords[i, 0],
                coords[i, 1],
                c=C_REUSE,
                s=160 if matched else 55,
                marker="*" if matched else "o",
                alpha=0.9 if matched else 0.4,
                edgecolors="white" if matched else "none",
                linewidths=0.6,
                zorder=4 if matched else 2,
            )

        for i in range(N):
            j = N + i
            matched = o_ids[i] in matched_orig_ids
            ax.scatter(
                coords[j, 0],
                coords[j, 1],
                c=C_ORIG,
                s=160 if matched else 55,
                marker="*" if matched else "o",
                alpha=0.9 if matched else 0.4,
                edgecolors="white" if matched else "none",
                linewidths=0.6,
                zorder=4 if matched else 2,
            )

        ax.legend(
            handles=[
                mpatches.Patch(
                    color=C_REUSE, alpha=0.7, label="DNZ article (reuse corpus)"
                ),
                mpatches.Patch(
                    color=C_ORIG, alpha=0.7, label="Das Kapital (original corpus)"
                ),
                plt.Line2D(
                    [0],
                    [0],
                    marker="*",
                    color="w",
                    markerfacecolor="#555",
                    markersize=11,
                    label="Detected quotation",
                ),
            ],
            loc="lower right",
            fontsize=9,
            framealpha=0.9,
            edgecolor="#cccccc",
        )

        ax.set_title(
            "Sentence embeddings: two corpora in the same semantic space\n"
            "Sentences with similar meaning cluster together across sources",
            fontsize=13,
            pad=12,
        )
        ax.set_xlabel("t-SNE dimension 1", fontsize=10)
        ax.set_ylabel("t-SNE dimension 2", fontsize=10)
        ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
        for spine in ax.spines.values():
            spine.set_visible(False)

        out = f"{OUT_DIR}/fig2_semantic_clusters.png"
        fig.savefig(out, dpi=180, bbox_inches="tight")
        plt.close(fig)
        print(f"  saved -> {out}")

    return (fig2_semantic_clusters,)


@app.cell
def _(
    C_MATCH,
    C_ORIG,
    OUT_DIR,
    SentenceTransformer,
    embed,
    np,
    pl,
    plt,
    textwrap,
):
    def fig3_similarity_bars(
        quotes: pl.DataFrame,
        reuse_df: pl.DataFrame,
        orig_df: pl.DataFrame,
        model: SentenceTransformer,
    ) -> None:
        """Plot cosine similarity of one reuse sentence against a sample of originals."""
        print("Building Figure 3 - similarity bar chart ...")

        N_BG = 29  # background original sentences to show alongside the match

        # pick best match with non-trivial text in both sides
        best = (
            quotes.filter(pl.col("reuse_text").str.len_chars() > 40)
            .filter(pl.col("original_text").str.len_chars() > 40)
            .sort("match_score", descending=True)
            .head(1)
        )
        focal_r_text = best["reuse_text"][0]
        focal_o_id = best["original_id"][0]
        focal_o_text = best["original_text"][0]
        match_score = best["match_score"][0]
        cosine_sim = 1.0 - match_score

        # sample N_BG other original sentences (not the match)
        bg_orig = (
            orig_df.filter(pl.col("sent_id") != focal_o_id)
            .filter(pl.col("text").str.len_chars() > 20)
            .sample(N_BG, seed=99)
        )
        bg_texts = bg_orig["text"].to_list()

        # embed reuse sentence + all candidate originals
        all_orig_texts = [focal_o_text, *bg_texts]
        orig_vecs = embed(all_orig_texts, model)
        reuse_vec = embed([focal_r_text], model)[0]

        # cosine similarities (vectors already normalised)
        sims = orig_vecs @ reuse_vec  # shape (N_BG+1,)

        # sort by similarity descending so the chart reads naturally
        order = np.argsort(-sims)
        sorted_sims = sims[order]
        match_pos = int(
            np.where(order == 0)[0][0]
        )  # position of the true match after sorting

        # build bar labels: short truncated text
        labels = []
        for _i, idx in enumerate(order):
            txt = focal_o_text if idx == 0 else bg_texts[idx - 1]
            short = txt[:38].replace("\n", " ") + "…"
            labels.append(short)

        N = len(sorted_sims)
        colors = [C_ORIG] * N
        colors[match_pos] = C_MATCH
        alphas = [0.35] * N
        alphas[match_pos] = 1.0

        fig, ax = plt.subplots(figsize=(12, 7))
        fig.patch.set_facecolor("#f8f8f8")
        ax.set_facecolor("#f8f8f8")

        bars = ax.barh(
            range(N), sorted_sims, color=colors, alpha=1.0, height=0.7, zorder=2
        )
        # apply per-bar alpha manually
        for bar, a in zip(bars, alphas, strict=False):
            bar.set_alpha(a)

        # annotate the match bar
        ax.annotate(
            f"  ← Detected match  (similarity {cosine_sim:.3f})",
            xy=(sorted_sims[match_pos], match_pos),
            xytext=(sorted_sims[match_pos] + 0.01, match_pos),
            fontsize=9,
            color=C_MATCH,
            va="center",
            fontweight="bold",
        )

        # y-axis labels
        ax.set_yticks(range(N))
        ax.set_yticklabels(labels, fontsize=7)
        ax.invert_yaxis()

        short_query = "\n".join(textwrap.wrap(focal_r_text[:130], 80))
        ax.set_xlabel(
            f'Cosine similarity to query sentence\n\nQuery (DNZ reuse sentence): "{short_query}"',
            fontsize=10,
            color="black",
            labelpad=12,
        )
        ax.set_title(
            "Embedding similarity: one reuse sentence vs. sample of Das Kapital sentences\n"
            "The true quotation source ranks highest",
            fontsize=12,
            pad=14,
        )
        ax.axvline(x=0, color="#aaaaaa", lw=0.8)
        for spine in ["top", "right"]:
            ax.spines[spine].set_visible(False)

        out = f"{OUT_DIR}/fig3_similarity_bars.png"
        fig.savefig(out, dpi=180, bbox_inches="tight")
        plt.close(fig)
        print(f"  saved -> {out}")

    return (fig3_similarity_bars,)


@app.cell
def _(
    C_MATCH,
    C_ORIG,
    C_REUSE,
    OUT_DIR,
    TSNE,
    SentenceTransformer,
    embed,
    mpatches,
    pl,
    plt,
    textwrap,
):
    def fig4_pair_neighbourhood(
        quotes: pl.DataFrame,
        reuse_df: pl.DataFrame,
        orig_df: pl.DataFrame,
        model: SentenceTransformer,
    ) -> None:
        """Plot the neighbourhood of a matched pair in t-SNE space."""
        print("Building Figure 4 - pair neighbourhood ...")

        N_NEIGHBOURS = 20  # context sentences per corpus around the focal pair

        # pick the best match with non-trivial text
        best = (
            quotes.filter(pl.col("reuse_text").str.len_chars() > 40)
            .filter(pl.col("original_text").str.len_chars() > 40)
            .sort("match_score")
            .head(1)
        )
        focal_r_id = best["reuse_id"][0]
        focal_o_id = best["original_id"][0]
        focal_r_text = best["reuse_text"][0]
        focal_o_text = best["original_text"][0]

        # sample neighbours (excluding the focal sentences)
        rng_seed = 42
        bg_reuse = (
            reuse_df.filter(pl.col("sent_id") != focal_r_id)
            .filter(pl.col("text").str.len_chars() > 20)
            .sample(N_NEIGHBOURS, seed=rng_seed)
        )
        bg_orig = (
            orig_df.filter(pl.col("sent_id") != focal_o_id)
            .filter(pl.col("text").str.len_chars() > 20)
            .sample(N_NEIGHBOURS, seed=rng_seed)
        )

        # embed: focal reuse, focal orig, bg reuse, bg orig
        all_texts = [
            focal_r_text,
            focal_o_text,
            *bg_reuse["text"].to_list(),
            *bg_orig["text"].to_list(),
        ]
        vecs = embed(all_texts, model)

        tsne = TSNE(n_components=2, perplexity=8, random_state=42, max_iter=2000)
        coords = tsne.fit_transform(vecs)

        focal_r_xy = coords[0]
        focal_o_xy = coords[1]
        bg_r_xy = coords[2 : 2 + N_NEIGHBOURS]
        bg_o_xy = coords[2 + N_NEIGHBOURS :]

        fig, ax = plt.subplots(figsize=(9, 7))
        fig.patch.set_facecolor("#f8f8f8")
        ax.set_facecolor("#f8f8f8")

        # background neighbours
        ax.scatter(bg_r_xy[:, 0], bg_r_xy[:, 1], c=C_REUSE, alpha=0.25, s=55, zorder=2)
        ax.scatter(bg_o_xy[:, 0], bg_o_xy[:, 1], c=C_ORIG, alpha=0.25, s=55, zorder=2)

        # dashed line connecting the matched pair
        ax.plot(
            [focal_r_xy[0], focal_o_xy[0]],
            [focal_r_xy[1], focal_o_xy[1]],
            color=C_MATCH,
            lw=1.8,
            linestyle="--",
            alpha=0.85,
            zorder=3,
        )

        # focal points
        ax.scatter(
            *focal_r_xy, c=C_REUSE, s=180, zorder=5, edgecolors="white", linewidths=1.2
        )
        ax.scatter(
            *focal_o_xy, c=C_ORIG, s=180, zorder=5, edgecolors="white", linewidths=1.2
        )

        # text labels on focal points
        short_r = textwrap.fill(focal_r_text[:80], 35) + "…"
        short_o = textwrap.fill(focal_o_text[:80], 35) + "…"
        ax.annotate(
            short_r,
            focal_r_xy,
            fontsize=7,
            color=C_REUSE,
            xytext=(10, 6),
            textcoords="offset points",
            bbox={
                "boxstyle": "round,pad=0.3",
                "facecolor": "#fff0ee",
                "edgecolor": C_REUSE,
                "alpha": 0.85,
            },
        )
        ax.annotate(
            short_o,
            focal_o_xy,
            fontsize=7,
            color=C_ORIG,
            xytext=(10, -28),
            textcoords="offset points",
            bbox={
                "boxstyle": "round,pad=0.3",
                "facecolor": "#e8f0f8",
                "edgecolor": C_ORIG,
                "alpha": 0.85,
            },
        )

        ax.legend(
            handles=[
                mpatches.Patch(color=C_REUSE, label="DNZ article sentence (reuse)"),
                mpatches.Patch(color=C_ORIG, label="Das Kapital sentence (original)"),
                plt.Line2D(
                    [0],
                    [0],
                    color=C_MATCH,
                    lw=1.8,
                    linestyle="--",
                    label="Detected quotation match",
                ),
            ],
            loc="lower right",
            fontsize=9,
            framealpha=0.9,
            edgecolor="#cccccc",
        )

        ax.set_title(
            "Neighbourhood of a detected quotation pair\nFocal sentences and surrounding context in embedding space",
            fontsize=13,
            pad=12,
        )
        ax.set_xlabel("t-SNE dimension 1", fontsize=10)
        ax.set_ylabel("t-SNE dimension 2", fontsize=10)
        ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
        for spine in ax.spines.values():
            spine.set_visible(False)

        out = f"{OUT_DIR}/fig4_pair_neighbourhood.png"
        fig.savefig(out, dpi=180, bbox_inches="tight")
        plt.close(fig)
        print(f"  saved → {out}")

    return (fig4_pair_neighbourhood,)


@app.cell
def _(
    OUT_DIR,
    fig1_matched_pairs,
    fig2_semantic_clusters,
    fig3_similarity_bars,
    fig4_pair_neighbourhood,
    load_data,
):
    print("Loading data and model …")
    quotes, reuse_df, orig_df, model = load_data()
    fig1_matched_pairs(quotes, reuse_df, orig_df, model)
    fig2_semantic_clusters(quotes, reuse_df, orig_df, model)
    fig3_similarity_bars(quotes, reuse_df, orig_df, model)
    fig4_pair_neighbourhood(quotes, reuse_df, orig_df, model)
    print("\nDone. All figures saved to", OUT_DIR)
    return model, orig_df, quotes, reuse_df


if __name__ == "__main__":
    app.run()
