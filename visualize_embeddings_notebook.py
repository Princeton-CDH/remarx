"""Generate embedding visualizations for the remarx presentation — Marimo notebook."""

import marimo

__generated_with = "0.10.0"
app = marimo.App(width="medium", app_title="Embedding Visualizations | remarx")


@app.cell
def _():
    import os
    import textwrap

    import matplotlib.patches as mpatches
    import matplotlib.pyplot as plt
    import numpy as np
    import polars as pl
    from sentence_transformers import SentenceTransformer
    from sklearn.manifold import TSNE

    os.environ["TOKENIZERS_PARALLELISM"] = "false"

    return TSNE, SentenceTransformer, mpatches, np, os, pl, plt, textwrap


@app.cell
def _():
    QUOTES_CSV = "/Users/ht8933/remarx-data/quotes/quote_pairs_6_originals_1896-97a XML Output-835pages.csv"
    REUSE_CSV = (
        "/Users/ht8933/remarx-data/corpora/reuse/1896-97a XML Output-835pages.csv"
    )
    ORIG_CSV = (
        "/Users/ht8933/remarx-data/corpora/original/Das_Kapital_MEGA_A2_B005-00_ETX.csv"
    )
    OUT_DIR = "/Users/ht8933/Documents/Documents-cdh-m5945fhwr7/dev/remarx"
    MODEL_NAME = "paraphrase-multilingual-mpnet-base-v2"

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
        return model.encode(texts, normalize_embeddings=True, show_progress_bar=False)

    return (embed,)


@app.cell
def _(MODEL_NAME, ORIG_CSV, QUOTES_CSV, REUSE_CSV, SentenceTransformer, pl):
    print("Loading data and model …")
    quotes = pl.read_csv(QUOTES_CSV, infer_schema_length=10000)
    reuse_df = pl.read_csv(REUSE_CSV, infer_schema_length=0)
    orig_df = pl.read_csv(ORIG_CSV, infer_schema_length=0)
    model = SentenceTransformer(MODEL_NAME)
    print("Done.")
    return model, orig_df, quotes, reuse_df


@app.cell
def _(
    C_MATCH,
    C_ORIG,
    C_REUSE,
    OUT_DIR,
    TSNE,
    embed,
    mpatches,
    model,
    np,
    orig_df,
    plt,
    quotes,
    reuse_df,
):
    # Figure 1 — Matched pairs in 2-D
    N_PAIRS = 15
    N_BG = 25

    best1 = (
        quotes.filter(__import__("polars").col("reuse_text").str.len_chars() > 40)
        .filter(__import__("polars").col("original_text").str.len_chars() > 40)
        .sort("match_score", descending=True)
        .head(N_PAIRS)
    )
    matched_reuse_ids1 = set(best1["reuse_id"].to_list())
    matched_orig_ids1 = set(best1["original_id"].to_list())

    import polars as _pl

    bg_reuse1 = reuse_df.filter(~_pl.col("sent_id").is_in(matched_reuse_ids1)).sample(
        N_BG, seed=42
    )
    bg_orig1 = orig_df.filter(~_pl.col("sent_id").is_in(matched_orig_ids1)).sample(
        N_BG, seed=42
    )

    matched_r_texts1 = best1["reuse_text"].to_list()
    matched_o_texts1 = best1["original_text"].to_list()
    bg_r_texts1 = bg_reuse1["text"].to_list()
    bg_o_texts1 = bg_orig1["text"].to_list()

    all_texts1 = matched_r_texts1 + matched_o_texts1 + bg_r_texts1 + bg_o_texts1
    vecs1 = embed(all_texts1, model)

    tsne1 = TSNE(n_components=2, perplexity=12, random_state=42, max_iter=2000)
    coords1 = tsne1.fit_transform(vecs1)

    mr_xy = coords1[:N_PAIRS]
    mo_xy = coords1[N_PAIRS : 2 * N_PAIRS]
    br_xy = coords1[2 * N_PAIRS : 2 * N_PAIRS + N_BG]
    bo_xy = coords1[2 * N_PAIRS + N_BG :]

    fig1, ax1 = plt.subplots(figsize=(10, 8))
    fig1.patch.set_facecolor("#f8f8f8")
    ax1.set_facecolor("#f8f8f8")

    ax1.scatter(br_xy[:, 0], br_xy[:, 1], c=C_REUSE, alpha=0.2, s=55, zorder=2)
    ax1.scatter(bo_xy[:, 0], bo_xy[:, 1], c=C_ORIG, alpha=0.2, s=55, zorder=2)

    for _i in range(N_PAIRS):
        ax1.plot(
            [mr_xy[_i, 0], mo_xy[_i, 0]],
            [mr_xy[_i, 1], mo_xy[_i, 1]],
            color=C_MATCH,
            lw=1.2,
            alpha=0.55,
            zorder=3,
        )

    ax1.scatter(
        mr_xy[:, 0],
        mr_xy[:, 1],
        c=C_REUSE,
        s=100,
        zorder=4,
        edgecolors="white",
        linewidths=0.8,
    )
    ax1.scatter(
        mo_xy[:, 0],
        mo_xy[:, 1],
        c=C_ORIG,
        s=100,
        zorder=4,
        edgecolors="white",
        linewidths=0.8,
    )

    for _i in range(4):
        ax1.annotate(
            matched_r_texts1[_i][:45].replace("\n", " ") + "…",
            mr_xy[_i],
            fontsize=6.5,
            color=C_REUSE,
            xytext=(6, 4),
            textcoords="offset points",
        )
        ax1.annotate(
            matched_o_texts1[_i][:45].replace("\n", " ") + "…",
            mo_xy[_i],
            fontsize=6.5,
            color=C_ORIG,
            xytext=(6, -10),
            textcoords="offset points",
        )

    ax1.legend(
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

    ax1.set_title(
        "Sentence embeddings in 2-D (t-SNE)\nMatched quotation pairs are connected",
        fontsize=13,
        pad=12,
    )
    ax1.set_xlabel("t-SNE dimension 1", fontsize=10)
    ax1.set_ylabel("t-SNE dimension 2", fontsize=10)
    ax1.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
    for _spine in ax1.spines.values():
        _spine.set_visible(False)

    fig1.savefig(f"{OUT_DIR}/fig1_matched_pairs.png", dpi=180, bbox_inches="tight")
    fig1


@app.cell
def _(
    C_ORIG,
    C_REUSE,
    OUT_DIR,
    TSNE,
    embed,
    mpatches,
    model,
    orig_df,
    plt,
    quotes,
    reuse_df,
):
    # Figure 2 — Two corpora in the same semantic space
    N2 = 120
    matched_reuse_ids2 = set(quotes["reuse_id"].to_list())
    matched_orig_ids2 = set(quotes["original_id"].to_list())

    sample_r2 = reuse_df.sample(N2, seed=7)
    sample_o2 = orig_df.sample(N2, seed=7)

    r_texts2 = sample_r2["text"].to_list()
    o_texts2 = sample_o2["text"].to_list()
    r_ids2 = sample_r2["sent_id"].to_list()
    o_ids2 = sample_o2["sent_id"].to_list()

    vecs2 = embed(r_texts2 + o_texts2, model)
    tsne2 = TSNE(n_components=2, perplexity=25, random_state=0, max_iter=2000)
    coords2 = tsne2.fit_transform(vecs2)

    fig2, ax2 = plt.subplots(figsize=(10, 8))
    fig2.patch.set_facecolor("#f8f8f8")
    ax2.set_facecolor("#f8f8f8")

    for _i in range(N2):
        _matched = r_ids2[_i] in matched_reuse_ids2
        ax2.scatter(
            coords2[_i, 0],
            coords2[_i, 1],
            c=C_REUSE,
            s=160 if _matched else 55,
            marker="*" if _matched else "o",
            alpha=0.9 if _matched else 0.4,
            edgecolors="white" if _matched else "none",
            linewidths=0.6,
            zorder=4 if _matched else 2,
        )

    for _i in range(N2):
        _j = N2 + _i
        _matched = o_ids2[_i] in matched_orig_ids2
        ax2.scatter(
            coords2[_j, 0],
            coords2[_j, 1],
            c=C_ORIG,
            s=160 if _matched else 55,
            marker="*" if _matched else "o",
            alpha=0.9 if _matched else 0.4,
            edgecolors="white" if _matched else "none",
            linewidths=0.6,
            zorder=4 if _matched else 2,
        )

    ax2.legend(
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

    ax2.set_title(
        "Sentence embeddings: two corpora in the same semantic space\n"
        "Sentences with similar meaning cluster together across sources",
        fontsize=13,
        pad=12,
    )
    ax2.set_xlabel("t-SNE dimension 1", fontsize=10)
    ax2.set_ylabel("t-SNE dimension 2", fontsize=10)
    ax2.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
    for _spine in ax2.spines.values():
        _spine.set_visible(False)

    fig2.savefig(f"{OUT_DIR}/fig2_semantic_clusters.png", dpi=180, bbox_inches="tight")
    fig2


@app.cell
def _(C_MATCH, C_ORIG, OUT_DIR, embed, model, np, orig_df, plt, quotes, textwrap):
    # Figure 3 — Similarity bar chart
    import polars as _pl3

    N_BG3 = 29

    best3 = (
        quotes.filter(_pl3.col("reuse_text").str.len_chars() > 40)
        .filter(_pl3.col("original_text").str.len_chars() > 40)
        .sort("match_score", descending=True)
        .head(1)
    )
    focal_r_text3 = best3["reuse_text"][0]
    focal_o_id3 = best3["original_id"][0]
    focal_o_text3 = best3["original_text"][0]
    cosine_sim3 = 1.0 - best3["match_score"][0]

    bg_orig3 = (
        orig_df.filter(_pl3.col("sent_id") != focal_o_id3)
        .filter(_pl3.col("text").str.len_chars() > 20)
        .sample(N_BG3, seed=99)
    )
    bg_texts3 = bg_orig3["text"].to_list()

    orig_vecs3 = embed([focal_o_text3, *bg_texts3], model)
    reuse_vec3 = embed([focal_r_text3], model)[0]
    sims3 = orig_vecs3 @ reuse_vec3

    order3 = np.argsort(-sims3)
    sorted_sims3 = sims3[order3]
    match_pos3 = int(np.where(order3 == 0)[0][0])

    labels3 = []
    for _idx in order3:
        _txt = focal_o_text3 if _idx == 0 else bg_texts3[_idx - 1]
        labels3.append(_txt[:38].replace("\n", " ") + "…")

    N3 = len(sorted_sims3)
    colors3 = [C_ORIG] * N3
    colors3[match_pos3] = C_MATCH
    alphas3 = [0.35] * N3
    alphas3[match_pos3] = 1.0

    fig3, ax3 = plt.subplots(figsize=(12, 7))
    fig3.patch.set_facecolor("#f8f8f8")
    ax3.set_facecolor("#f8f8f8")

    bars3 = ax3.barh(
        range(N3), sorted_sims3, color=colors3, alpha=1.0, height=0.7, zorder=2
    )
    for _bar, _a in zip(bars3, alphas3, strict=False):
        _bar.set_alpha(_a)

    ax3.annotate(
        f"  ← Detected match  (similarity {cosine_sim3:.3f})",
        xy=(sorted_sims3[match_pos3], match_pos3),
        xytext=(sorted_sims3[match_pos3] + 0.01, match_pos3),
        fontsize=9,
        color=C_MATCH,
        va="center",
        fontweight="bold",
    )

    ax3.set_yticks(range(N3))
    ax3.set_yticklabels(labels3, fontsize=7)
    ax3.invert_yaxis()

    _short_query = "\n".join(textwrap.wrap(focal_r_text3[:130], 80))
    ax3.set_xlabel(
        f'Cosine similarity to query sentence\n\nQuery (DNZ reuse sentence): "{_short_query}"',
        fontsize=10,
        labelpad=12,
    )
    ax3.set_title(
        "Embedding similarity: one reuse sentence vs. sample of Das Kapital sentences\n"
        "The true quotation source ranks highest",
        fontsize=12,
        pad=14,
    )
    ax3.axvline(x=0, color="#aaaaaa", lw=0.8)
    for _spine in ["top", "right"]:
        ax3.spines[_spine].set_visible(False)

    fig3.savefig(f"{OUT_DIR}/fig3_similarity_bars.png", dpi=180, bbox_inches="tight")
    fig3


@app.cell
def _(
    C_MATCH,
    C_ORIG,
    C_REUSE,
    OUT_DIR,
    TSNE,
    embed,
    mpatches,
    model,
    orig_df,
    plt,
    quotes,
    reuse_df,
    textwrap,
):
    # Figure 4 — Pair neighbourhood
    import polars as _pl4

    N_NEIGHBOURS4 = 20

    best4 = (
        quotes.filter(_pl4.col("reuse_text").str.len_chars() > 40)
        .filter(_pl4.col("original_text").str.len_chars() > 40)
        .sort("match_score")
        .head(1)
    )
    focal_r_id4 = best4["reuse_id"][0]
    focal_o_id4 = best4["original_id"][0]
    focal_r_text4 = best4["reuse_text"][0]
    focal_o_text4 = best4["original_text"][0]

    bg_reuse4 = (
        reuse_df.filter(_pl4.col("sent_id") != focal_r_id4)
        .filter(_pl4.col("text").str.len_chars() > 20)
        .sample(N_NEIGHBOURS4, seed=42)
    )
    bg_orig4 = (
        orig_df.filter(_pl4.col("sent_id") != focal_o_id4)
        .filter(_pl4.col("text").str.len_chars() > 20)
        .sample(N_NEIGHBOURS4, seed=42)
    )

    all_texts4 = [
        focal_r_text4,
        focal_o_text4,
        *bg_reuse4["text"].to_list(),
        *bg_orig4["text"].to_list(),
    ]
    vecs4 = embed(all_texts4, model)

    tsne4 = TSNE(n_components=2, perplexity=8, random_state=42, max_iter=2000)
    coords4 = tsne4.fit_transform(vecs4)

    focal_r_xy4 = coords4[0]
    focal_o_xy4 = coords4[1]
    bg_r_xy4 = coords4[2 : 2 + N_NEIGHBOURS4]
    bg_o_xy4 = coords4[2 + N_NEIGHBOURS4 :]

    fig4, ax4 = plt.subplots(figsize=(9, 7))
    fig4.patch.set_facecolor("#f8f8f8")
    ax4.set_facecolor("#f8f8f8")

    ax4.scatter(bg_r_xy4[:, 0], bg_r_xy4[:, 1], c=C_REUSE, alpha=0.25, s=55, zorder=2)
    ax4.scatter(bg_o_xy4[:, 0], bg_o_xy4[:, 1], c=C_ORIG, alpha=0.25, s=55, zorder=2)

    ax4.plot(
        [focal_r_xy4[0], focal_o_xy4[0]],
        [focal_r_xy4[1], focal_o_xy4[1]],
        color=C_MATCH,
        lw=1.8,
        linestyle="--",
        alpha=0.85,
        zorder=3,
    )

    ax4.scatter(
        *focal_r_xy4, c=C_REUSE, s=180, zorder=5, edgecolors="white", linewidths=1.2
    )
    ax4.scatter(
        *focal_o_xy4, c=C_ORIG, s=180, zorder=5, edgecolors="white", linewidths=1.2
    )

    ax4.annotate(
        textwrap.fill(focal_r_text4[:80], 35) + "…",
        focal_r_xy4,
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
    ax4.annotate(
        textwrap.fill(focal_o_text4[:80], 35) + "…",
        focal_o_xy4,
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

    ax4.legend(
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

    ax4.set_title(
        "Neighbourhood of a detected quotation pair\nFocal sentences and surrounding context in embedding space",
        fontsize=13,
        pad=12,
    )
    ax4.set_xlabel("t-SNE dimension 1", fontsize=10)
    ax4.set_ylabel("t-SNE dimension 2", fontsize=10)
    ax4.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
    for _spine in ax4.spines.values():
        _spine.set_visible(False)

    fig4.savefig(f"{OUT_DIR}/fig4_pair_neighbourhood.png", dpi=180, bbox_inches="tight")
    fig4


if __name__ == "__main__":
    app.run()
