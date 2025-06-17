import marimo

__generated_with = "0.13.11"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import polars as pl
    import chromadb
    return chromadb, mo, np, pl


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # Try out Chromadb for finding similar sentences

    Using the sample sentence corpora and embeddings generated in previous steps.

    We'll try this two different ways: 

    1. Index DNZ sentence embeddings and query with Marx sentence embeddings
    2. Index Marx sentence embeddings and query with DNZ sentence embeddings
    """
    )
    return


@app.cell
def _(chromadb):
    # use EphemeralClient for an in-memory, since this is a small test-set of content
    chroma_client = chromadb.EphemeralClient()

    dnz_collection = chroma_client.get_or_create_collection(name="dnz_sentences")
    marx_collection = chroma_client.get_or_create_collection(name="marx_sentences")
    return dnz_collection, marx_collection


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""Load sample sentence corpora and embeddings, and load into the chroma collection."""
    )
    return


@app.cell
def _(np, pl):
    dnz_sentences = np.load("data/sentence-embeddings/dnz-sample-sents.npy")
    # load newline-delimited json (aka JSON lines) into lazy frame, then collect
    dnz_sentences_df = pl.scan_ndjson(
        "data/sentence-corpora/dnz-sample-sents.jsonl"
    ).collect()
    dnz_sentences_df
    return dnz_sentences, dnz_sentences_df


@app.cell
def _(dnz_collection, dnz_sentences, dnz_sentences_df):
    # add DNZ sentences and pre-computed embeddings to chroma DNZ collection
    dnz_collection.add(
        documents=dnz_sentences_df["text"].to_list(),
        ids=dnz_sentences_df["sent_id"].to_list(),
        embeddings=dnz_sentences,
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""Load sample sentences and embeddings for test pages from MEGA.""")
    return


@app.cell
def _(np, pl):
    mega_sentence_embed = np.load(
        "data/sentence-embeddings/mega-sample-sents.npy", allow_pickle=True
    )
    # load newline-delimited json (aka JSON lines) into lazy frame, then collect
    mega_sent_df = pl.scan_ndjson(
        "data/sentence-corpora/mega-sample-sents.jsonl"
    ).collect()
    mega_sent_df
    return mega_sent_df, mega_sentence_embed


@app.cell
def _(marx_collection, mega_sent_df, mega_sentence_embed):
    # add mega sentences and pre-computed embeddings to chroma mega collection
    marx_collection.add(
        documents=mega_sent_df["text"].to_list(),
        ids=mega_sent_df["sent_id"].to_list(),
        embeddings=mega_sentence_embed,
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    Query DNZ chroma collection for similar sentences for every sentence embedding for the MEGA content. Request the response result to return documents and distances (ids are always returned).

    This returns a list of lists; "ids" is a list of items; for N results for each embedding that was submitted. Similarly for the other fields, there is a list of lists with N results for each embedding queried.
    """
    )
    return


@app.cell
def _(dnz_collection, mega_sentence_embed):
    # query all embeddings and return 10 for each
    result = dnz_collection.query(
        query_embeddings=mega_sentence_embed,
        n_results=10,
        include=["documents", "distances"],
    )
    # uncomment to see structure
    # result
    return (result,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""Load the input sentences and ids and query results into a dataframe and restructure, so that the input text and result text can be seen together. If desired, this can be exported for comparison + review in a spreadsheet."""
    )
    return


@app.cell
def _(mega_sent_df, pl, result):
    dnz_query_marx_result_df = pl.DataFrame(
        data={
            "id": mega_sent_df["sent_id"].to_list(),
            "input_text": mega_sent_df["text"].to_list(),
            "result_text": result["documents"],
            "distance": result["distances"],
            "result_id": result["ids"],
        }
    ).explode("result_id", "result_text", "distance")

    # result_df.write_csv("mega_dnz_chroma.csv")
    dnz_query_marx_result_df
    return (dnz_query_marx_result_df,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""Now do the same thing in the other direction: query the collection loaded with Marx content for DNZ sentences."""
    )
    return


@app.cell
def _(dnz_sentences, marx_collection):
    # query all embeddings and return 10 for each
    marx_query_dnz_result = marx_collection.query(
        query_embeddings=dnz_sentences,
        n_results=10,
        include=["documents", "distances"],
    )
    return (marx_query_dnz_result,)


@app.cell
def _(dnz_sentences_df, marx_query_dnz_result, pl):
    marx_query_dnz_result_df = pl.DataFrame(
        data={
            "id": dnz_sentences_df["sent_id"].to_list(),
            "input_text": dnz_sentences_df["text"].to_list(),
            "result_text": marx_query_dnz_result["documents"],
            "distance": marx_query_dnz_result["distances"],
            "result_id": marx_query_dnz_result["ids"],
        }
    ).explode("result_id", "result_text", "distance")

    marx_query_dnz_result_df
    return (marx_query_dnz_result_df,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""Use the set of known Marx/DNZ sentence pairs for some initial evaluation."""
    )
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


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    For each sentence pair from our evaluation data, find and report on the similarity results for querying in both directions.

    - What is the rank/order in each direction?
    - What is the distance score?
    - What are the adjacent distance scores (next closest if any, next farthest)
    - How many sentence pairs overlap in searching for the two
    """
    )
    return


@app.cell
def _(dnz_query_marx_result_df, eval_pairs_df, marx_query_dnz_result_df, pl):
    results = []

    for eval_pair in eval_pairs_df.iter_rows(named=True):
        # for results from indexing marx and querying dnz:
        # - filter to this dnz sentence, sort by distance, add row index
        marx_q_dnz_results = (
            marx_query_dnz_result_df.filter(
                pl.col("id").eq(eval_pair["dnz_sent_id"])
            )
            .sort(pl.col("distance"))
            .with_row_index()
        )
        # filter to this marx sentence to get rank
        eval_match = marx_q_dnz_results.filter(
            pl.col("result_id").eq(eval_pair["marx_sent_id"])
        ).row(0, named=True)
        marx_index_rank = eval_match["index"]
        marx_index_distance = eval_match["distance"]
        # what is the next closest sentence?
        marx_next_closest = marx_q_dnz_results.row(
            marx_index_rank + 1, named=True
        )["distance"]

        # do the same thing for the other set, indexing dnz and querying marx
        dnz_q_marx_results = (
            dnz_query_marx_result_df.filter(
                pl.col("id").eq(eval_pair["marx_sent_id"])
            )
            .sort(pl.col("distance"))
            .with_row_index()
        )
        # filter to this dnz sentence to get rank
        dnz_eval_match = dnz_q_marx_results.filter(
            pl.col("result_id").eq(eval_pair["dnz_sent_id"])
        ).row(0, named=True)
        dnz_index_rank = eval_match["index"]
        dnz_index_distance = eval_match["distance"]
        # what is the next closest sentence?
        dnz_next_closest = dnz_q_marx_results.row(marx_index_rank + 1, named=True)[
            "distance"
        ]

        # determine how many many overlapping pairs in these two sets of results
        # make a set of id pair tuples
        dnq_q_marx_ids = set(
            (row["id"], row["result_id"])
            for row in marx_q_dnz_results.iter_rows(named=True)
        )
        # swap id/result id order so we always list marx sentence id first
        marx_q_dnz_ids = set(
            (row["result_id"], row["id"])
            for row in dnz_q_marx_results.iter_rows(named=True)
        )
        overlap_count = len(dnq_q_marx_ids & marx_q_dnz_ids)

        results.append(
            {
                "marx_sent_id": eval_pair["marx_sent_id"],
                "dnz_sent_id": eval_pair["dnz_sent_id"],
                "marx_index_rank": marx_index_rank,
                # "marx_index_distance": marx_index_distance,
                "dnz_index_rank": dnz_index_rank,
                # "dnz_index_distance": dnz_index_distance,
                # distance is the same either way
                "distance": marx_index_distance,
                "marx_next_closest": marx_next_closest,
                "dnz_next_closest": dnz_next_closest,
                "dnz_marx_q_overlap": overlap_count,
                "comments": eval_pair["comments"],
            }
        )

    results_df = pl.from_dicts(results)
    # save a copy of this dataframe
    results_df.write_csv("data/sentence-pairs/chroma-eval-pairs.csv")

    results_df
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    In every case but one, the expected sentence pair shows up as the closest match when searching in either direction. 

    When we check the overlap between the two searches, the expected sentence pair is the only overlap - although this may be an artifact of querying with the small dataset we're testing with.

    The sentence that shows up at index 4 is noted as an accurate citation that is unedited, but the quotation is about half (or less) of the full sentence in DNZ as it is currently tokenized. 

    ---
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""Compare the similar sentences found searching the two different directions. How much overlap is there?"""
    )
    return


@app.cell
def _(dnz_query_marx_result_df, marx_query_dnz_result_df, pl):
    all_sent_pairs_df = pl.concat(
        [
            dnz_query_marx_result_df.select(
                pl.col("id").alias("marx_sent_id"),
                pl.col("result_id").alias("dnz_sent_id"),
            ),
            marx_query_dnz_result_df.select(
                pl.col("result_id").alias("marx_sent_id"),
                pl.col("id").alias("dnz_sent_id"),
            ),
        ]
    )

    print(
        f"{all_sent_pairs_df.height:,} total sentence pairs for querying in both directions"
    )
    dupe_sentence_pairs = all_sent_pairs_df.filter(
        all_sent_pairs_df.is_duplicated()
    )
    print(
        f"{dupe_sentence_pairs.height:,} duplicated sentence pairs across the two sets of results"
    )
    return


if __name__ == "__main__":
    app.run()
