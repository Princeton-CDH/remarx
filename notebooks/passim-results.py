import marimo

__generated_with = "0.14.16"
app = marimo.App(
    width="medium",
    app_title="Passim evaluation",
    css_file="highlight.css",
)


@app.cell
def _():
    import marimo as mo
    import polars as pl
    return mo, pl


@app.cell
def _(pl):
    df = pl.read_ndjson(
        "data/passim/output/default/out.json/part-00000-dbd8cab7-6c9f-4866-b676-ff2bcd4b0890-c000.json"
    )
    df
    return (df,)


@app.cell
def _(df, mo):
    unique_clusters = len(df["cluster"].unique())
    cluster_sizes = ",".join([str(s) for s in df["size"].unique().to_list()])

    mo.md(f"Found **{unique_clusters}** clusters of size **{cluster_sizes}**.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""This output shows the matching text content from the two texts.""")
    return


@app.cell
def _(df, mo, pl):
    output = []

    for cluster, rows in df.group_by("cluster"):
        dnz_content = rows.filter(pl.col("series") == "dnz").row(0, named=True)
        mega_content = rows.filter(pl.col("series") == "mega").row(0, named=True)

        output.append(f"#### {dnz_content['id']} <> MEGA {mega_content['id']}")
        output.append("**DNZ text:**\n")
        output.append(dnz_content["text"])
        output.append("\n**MEGA text:**\n")
        output.append(mega_content["text"])
        output.append("---")


    mo.md("\n".join(output))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""Load sentence corpora and use character indices to get a list of sentences overlapping with the passages found by passim.""")
    return


@app.cell
def _(pl):
    marx_sentences = pl.read_ndjson(
        "data/sentence-corpora/mega-sample-sents.jsonl"
    )
    # calculate sentence end index
    marx_sentences = marx_sentences.with_columns(
        char_end_idx=pl.col("char_idx").add(pl.col("text").str.len_chars())
    )
    dnz_sentences = pl.read_ndjson(
        ("data/sentence-corpora/dnz-sample-sents.jsonl")
    )
    # calculate sentence end index
    dnz_sentences = dnz_sentences.with_columns(
        char_end_idx=pl.col("char_idx").add(pl.col("text").str.len_chars())
    )
    return dnz_sentences, marx_sentences


@app.cell
def _(df, dnz_sentences, marx_sentences, pl):
    # passim id is filename without extensin; add it back for matching
    passim_df = df.with_columns(file=pl.col("id") + pl.lit(".txt"))
    # combine sentence corpora into a single dataframe
    all_sentences = pl.concat([marx_sentences, dnz_sentences])

    # then do a conditional join to get sentence ids for passim results
    passim_df = passim_df.join_where(
        all_sentences,
        # join based on filename and any overlapping characters
        # we expect multiple sentences for several of the passages found by passim
        pl.col("file") == pl.col("file_right"),
        pl.col("begin") < pl.col("char_end_idx"),
        pl.col("end") > pl.col("char_idx"),
    )
    # select the fields we need to keep for evaluation
    passim_df = passim_df.select(
        "cluster",
        "file",
        "sent_id",
        "series",
        "begin",
        "end",
        "char_idx",
        "char_end_idx",
        "text",
        "text_right",
    )
    return (passim_df,)


@app.cell
def _(passim_df, pl):
    # get a list of all sentences for each series
    passim_marx_sent_ids = set(
        passim_df.filter(pl.col("series") == "mega")["sent_id"].to_list()
    )
    passim_dnz_sent_ids = set(
        passim_df.filter(pl.col("series") == "dnz")["sent_id"].to_list()
    )
    return passim_dnz_sent_ids, passim_marx_sent_ids


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""Load evaluation data and sentence corpora for comparison and evaluation of passim results.""")
    return


@app.cell
def _(pl):
    # load the evaulation data and filter to those that have sentence ids for both sentence corpora
    eval_pairs_df = pl.read_csv(
        "data/sentence-eval-pairs/dnz_marx_sentence_pairs.csv"
    )
    eval_pairs_df = eval_pairs_df.filter(
        pl.col("marx_sent_id").is_not_null(), pl.col("dnz_sent_id").is_not_null()
    )
    eval_pairs_df
    return (eval_pairs_df,)


@app.cell
def _(eval_pairs_df, mo, passim_dnz_sent_ids, passim_marx_sent_ids):
    # what is the overlap between sentence ids?
    eval_marx_sent_ids = set(eval_pairs_df["marx_sent_id"].to_list())
    eval_dnz_sent_ids = set(eval_pairs_df["dnz_sent_id"].to_list())

    passim_marx_sent_ids.issuperset(eval_marx_sent_ids)
    # in common
    passim_marx_sent_ids & eval_marx_sent_ids
    # passim_marx_sent_ids

    # report on how they match up
    mo.md(f"""## Passim sentence id comparison

    Comparing passim matches with sentence evaluation pairs based on sentence id. For passim, we include any sentence that overlaps with the passage.

    ### Marx sentences
    - {len(eval_marx_sent_ids)} marx sentence ids in evaluation data.
    - {len(passim_marx_sent_ids)} marx sentence ids in passim results.
    - {len(eval_marx_sent_ids & passim_marx_sent_ids)} sentence ids in common.
    - {len(passim_marx_sent_ids - eval_marx_sent_ids)} sentence ids in passim results not in evaluation data:
    > {(passim_marx_sent_ids - eval_marx_sent_ids)}

    ### DNZ sentences
    - {len(eval_dnz_sent_ids)} marx sentence ids in evaluation data.
    - {len(passim_dnz_sent_ids)} marx sentence ids in passim results.
    - {len(eval_dnz_sent_ids & passim_dnz_sent_ids)} sentence ids in common.
    - {len(passim_dnz_sent_ids - eval_dnz_sent_ids)} sentence ids in passim results not in evaluation data:
    > {(passim_dnz_sent_ids - eval_dnz_sent_ids)}

    """)
    return


@app.cell
def _(eval_pairs_df, marx_sentences, pl):
    # join marx and dnz sentences in order to get character indices for highlighting
    eval_df = eval_pairs_df.join(
        marx_sentences.select("sent_id", "file", "char_idx", "char_end_idx"),
        left_on=pl.col("marx_sent_id"),
        right_on=pl.col("sent_id"),
        how="left",
    ).rename(
        {
            "char_idx": "marx_start_index",
            "char_end_idx": "marx_end_index",
            "file": "marx_file",
        }
    )
    return


@app.cell
def _(dnz_sentences, eval_pairs_df, pl):
    # get the DNZ sentences in our evaluation pairs, so we can highlight them
    dnz_eval_sent_ids = eval_pairs_df["dnz_sent_id"].unique().to_list()
    dnz_eval_sents = dnz_sentences.filter(
        pl.col("sent_id").is_in(dnz_eval_sent_ids)
    )
    dnz_eval_sents
    return (dnz_eval_sents,)


@app.cell(hide_code=True)
def _(mo, passim_df):
    uniq_clusters = passim_df["cluster"].unique().to_list()
    cluster_slider = mo.ui.slider(
        start=0,
        stop=len(uniq_clusters) - 1,
        step=1,
        label="passim cluster",
    )
    cluster_slider
    return cluster_slider, uniq_clusters


@app.cell(hide_code=True)
def _(cluster_slider, dnz_eval_sents, mo, passim_df, pl, uniq_clusters):
    # create panels with highlighted text
    from remarx.highlight_utils import highlight_spans


    def highlight_passim_passages():
        # get cluster id
        cluster_id = uniq_clusters[cluster_slider.value]
        # find passim passages for dnz text in cluster
        passim_passages = passim_df.filter(
            pl.col("cluster").eq(cluster_id),
            pl.col("series").eq("dnz"),
        )
        dnz_filename = passim_passages.row(0, named=True)["file"]
        with open(f"data/dnz-sample-articles/{dnz_filename}") as dnzfile:
            dnztext = dnzfile.read()

        spans = passim_passages.select("char_idx", "char_end_idx").rows()

        highlighted_text = highlight_spans(dnztext, spans)
        # subset the text around the quotes with some padding
        min_index = passim_passages["char_idx"].min() - 150
        max_index = passim_passages["char_end_idx"].max() + 350

        highlighted_text = highlighted_text[min_index:max_index]
        return cluster_id, highlighted_text, dnz_filename, min_index, max_index


    def passim_panel(cluster_id, highlighted_text):
        return mo.Html(
            "<section class='page'><header><h1>passim</h2>"
            + f"<p class='info'>cluster {cluster_id}</p></header>"
            + highlighted_text
            + "</section>"
        )


    def highlight_sentence_pairs(dnz_filename, min_index, max_index):
        eval_subset = dnz_eval_sents.filter(
            pl.col("file").eq(dnz_filename),
            pl.col("char_idx") < max_index,
            pl.col("char_end_idx") > min_index,
        )
        spans = eval_subset.select("char_idx", "char_end_idx").rows()

        with open(f"data/dnz-sample-articles/{dnz_filename}") as dnzfile:
            dnztext = dnzfile.read()

        return highlight_spans(dnztext, spans)[min_index:max_index]


    def eval_panel(text):
        return mo.Html(
            "<section class='page highlight2'><header><h1>evaluation sentence pairs</h2></header>"
            + text
            + "</section>"
        )


    cluster_id, highlighted_text, dnz_filename, min_index, max_index = (
        highlight_passim_passages()
    )

    mo.hstack(
        [
            passim_panel(cluster_id, highlighted_text),
            eval_panel(
                highlight_sentence_pairs(dnz_filename, min_index, max_index)
            ),
        ],
        justify="center",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## Conclusion

    All of the sentence in our evaluation pairs are found by passim.

    Passim also finds additional sentences; the sentences found are around the passages of interest, so passim is identifying extra content we did not include before or after the quote.

    The gaps in some of the quotations also means that passim groups interrupted quotes in different clusters.
    """
    )
    return


if __name__ == "__main__":
    app.run()
