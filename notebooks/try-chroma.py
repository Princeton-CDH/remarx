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

    collection = chroma_client.get_or_create_collection(name="marx_test")
    return (collection,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""Load sample sentence corpora and embeddings, and load into the chroma collection."""
    )
    return


@app.cell
def _(np, pl):
    dnz_sentences = np.load(
        "data/sentence-embeddings/dnz-sample-sents.npy", allow_pickle=True
    )
    # load newline-delimited json (aka JSON lines) into lazy frame, then collect
    df = pl.scan_ndjson("data/sentence-corpora/dnz-sample-sents.jsonl").collect()
    df
    return df, dnz_sentences


@app.cell
def _(collection, df, dnz_sentences):
    # add sentences and pre-computed embeddings to chroma collection
    collection.add(
        documents=df["text"].to_list(),
        ids=df["sent_id"].to_list(),
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
def _(collection, mega_sentence_embed):
    # query all embeddings and return 10 for each
    result = collection.query(
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
        r"""Load the input sentences and ids and query result into a dataframe and restructure, then save for comparison + review in a spreadsheet."""
    )
    return


@app.cell
def _(mega_sent_df, pl, result):
    result_df = pl.DataFrame(
        data={
            "id": mega_sent_df["sent_id"].to_list(),
            "input_text": mega_sent_df["text"].to_list(),
            "result_text": result["documents"],
            "distance": result["distances"],
            "result_id": result["ids"],
        }
    ).explode("result_id", "result_text", "distance")

    result_df.write_csv("mega_dnz_chroma.csv")
    result_df
    return


if __name__ == "__main__":
    app.run()
