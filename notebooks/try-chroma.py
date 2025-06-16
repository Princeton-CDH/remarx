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
    """
    )
    return


@app.cell
def _(chromadb):
    chroma_client = chromadb.EphemeralClient()  # using EphemeralClient for in-memory, since this is a small test-set of content

    dnz_collection = chroma_client.get_or_create_collection(name="dnz_sentences")
    marx_collection = chroma_client.get_or_create_collection(name="marx_sentences")
    return dnz_collection, marx_collection


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""Load sample sentence corpora and embeddings, and load into the chroma collection.""")
    return


@app.cell
def _(np, pl):
    dnz_sentences = np.load(
        "data/sentence-embeddings/dnz-sample-sents.npy"
    )
    # load newline-delimited json (aka JSON lines) into lazy frame, then collect
    dnz_sentences_df = pl.scan_ndjson("data/sentence-corpora/dnz-sample-sents.jsonl").collect()
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
    Query chroma for similar sentences for every sentence embedding for the MEGA content. Request the response result to return documents and distances (ids are always returned).

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
    mo.md(r"""Load the input sentences and ids and query result into a dataframe and restructure, then save for comparison + review in a spreadsheet.""")
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

    #result_df.write_csv("mega_dnz_chroma.csv")
    dnz_query_marx_result_df
    return (dnz_query_marx_result_df,)


@app.cell
def _(dnz_sentences, marx_collection):
    # now do the reverse direction: query marx for dnz sentences

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


@app.cell
def _(pl):
    # compare results for one id in both directions
    # - check one of the known sentence evaluation pairs

    eval_pairs_df = pl.read_csv("data/sentence-eval-pairs/dnz_marx_sentence_pairs.csv")
    eval_pairs_df = eval_pairs_df.filter(pl.col("mega_sent_id").is_not_null(), pl.col("dnz_sent_id").is_not_null())
    eval_pairs_df
    return (eval_pairs_df,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""Let's look at the first paired sentence example and see what results we get for queries in both directions.""")
    return


@app.cell
def _(eval_pairs_df, mo):
    example_index = mo.ui.slider(start=0, stop=eval_pairs_df.height - 1, label='Example sentence pair:')
    example_index
    return (example_index,)


@app.cell
def _(eval_pairs_df, example_index, marx_query_dnz_result_df, pl):
    example = eval_pairs_df.row(example_index.value, named=True)
    # mega_sent_id, dnz_sent_id

    # filter to results for this sentence, sort by distance, add row index
    example_marx_results = marx_query_dnz_result_df.filter(pl.col("id").eq(example["dnz_sent_id"])).sort(pl.col('distance')).with_row_index()
    example_marx_results
    return example, example_marx_results


@app.cell
def _(example, example_marx_results, pl):
    # where does the known matching sentence id rank? 
    # it's the closest match! (for first 3 examples; index 4 for example 3)
    example_marx_results.filter(pl.col("result_id").eq(example['mega_sent_id']))
    return


@app.cell
def _(dnz_query_marx_result_df, example, pl):
    # now do the same thing for the queries made in the other direction (index dnz and query marx sentences)

    example_dnz_results = dnz_query_marx_result_df.filter(pl.col("id").eq(example["mega_sent_id"])).sort(pl.col("distance")).with_row_index()

    example_dnz_results
    return (example_dnz_results,)


@app.cell
def _(example, example_dnz_results, pl):
    # when we indexed marx text and queried for dnz sentences...
    # - first and third example, matching sentence pair is the closest match (row 0)
    # - second and fourth examples are second match (row 1)
    example_dnz_results.filter(pl.col('result_id').eq(example['dnz_sent_id']))
    return


@app.cell
def _(example_dnz_results, example_marx_results):
    # how much do these sets of most similar sentences overlap?

    # make a set of id pair tuples
    dnq_q_marx_ids = set((row['id'], row['result_id']) for row in example_dnz_results.iter_rows(named=True))
    # swap id/result id order so we always list marx sentence id first
    marx_q_dnz_ids = set((row['result_id'], row['id']) for row in example_marx_results.iter_rows(named=True))

    # we get exactly one sentence overlap, which is in fact our expected sentence pair
    dnq_q_marx_ids & marx_q_dnz_ids
    return


@app.cell
def _(example):
    # what's the expected pair?
    print(example['mega_sent_id'], example['dnz_sent_id'])
    return


@app.cell
def _():
    # todo
    # rewrite this to simplify output and report on ALL pairs in our current data
    # - rank in each direction
    # - distance score
    # ... nearby distances? (closer/farther?)
    # number of overlap between top ten when querying both directions; is it always true that it is only our pair? is that useful?

    return


if __name__ == "__main__":
    app.run()
