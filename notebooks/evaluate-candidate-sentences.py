

import marimo

__generated_with = "0.13.2"
app = marimo.App(width="medium", auto_download=["html"])


@app.cell
def _():
    import csv
    import marimo as mo
    import polars as pl
    from collections import defaultdict
    from itertools import chain

    from remarx.polar_utils import (
        join_candidates_annotation,
        join_candidates_ner,
        load_candidate_sentences,
        load_flair_ner,
        load_title_annotations,
        load_title_phrases,
    )
    return (
        chain,
        join_candidates_annotation,
        join_candidates_ner,
        load_candidate_sentences,
        load_flair_ner,
        load_title_annotations,
        load_title_phrases,
        mo,
        pl,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md("""## Load Data""")
    return


@app.cell(hide_code=True)
def _():
    ### Load title search phrases
    return


@app.cell
def _(load_title_phrases):
    # Load title phrases
    title_phrases = load_title_phrases()
    title_phrases
    return (title_phrases,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""### Load "candidate" sentences identified through lemmatized phrase search""")
    return


@app.cell
def _(load_candidate_sentences, title_phrases):
    # Load candidate sentences
    candidates = load_candidate_sentences(
        "data/candidate_mentions/title_mentions.csv", title_phrases
    )
    candidates
    return (candidates,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ### Load manual title mentions annotations

        We consider quote annotations as possible title mentions marked as "Maybe".
        """
    )
    return


@app.cell
def _(load_title_annotations):
    # Load title annotations
    annotations = load_title_annotations()
    annotations
    return (annotations,)


@app.cell(hide_code=True)
def _():
    ### Match candidate sentences with manual annotations
    return


@app.cell
def _(annotations, candidates, join_candidates_annotation):
    annotated_candidates = join_candidates_annotation(candidates, annotations)
    annotated_candidates.unique("lem_phrases")
    return (annotated_candidates,)


@app.cell
def _(annotated_candidates, annotations, mo, pl):
    # get number of unannotated candidates
    n_unannotated = annotated_candidates.filter(
        pl.col("anno_uuid") == "N/A"
    ).shape[0]


    # get number of unmatched annotations
    n_unmatched = annotations.filter(
        ~pl.col("anno_uuid").is_in(
            annotated_candidates.get_column("anno_uuid").to_list()
        )
    ).shape[0]

    mo.md(
        f"""
        Unannotated Candidate Sentences: {n_unannotated}

        Unmatched Annotations: {n_unmatched}
        """
    )
    return (n_unmatched,)


@app.cell
def _(mo):
    mo.md(r"""### Add flair results""")
    return


@app.cell(hide_code=True)
def _(load_flair_ner, pl):
    # Load & prep flair results
    flair_results = (
        load_flair_ner()
        .filter(
            (
                pl.col("flair_span_text")
                .str.to_lowercase()
                .str.contains("band|kapital|manifest")
            )
        )
        .with_columns(
            pl.col("flair_span_text")
            .str.to_lowercase()
            .str.contains("band")
            .alias("flair_contains_band"),
            pl.col("flair_span_text")
            .str.to_lowercase()
            .str.contains("kapital")
            .alias("flair_contains_kapital"),
            pl.col("flair_span_text")
            .str.to_lowercase()
            .str.contains("manifest")
            .alias("flair_contains_manifest"),
        )
        .sort(["flair_ner_tag", "flair_span_text"])
    )
    flair_results
    return (flair_results,)


@app.cell
def _(annotated_candidates, flair_results, join_candidates_ner):
    # Join flair results to annotated candidates
    final_annotated_candidates = join_candidates_ner(
        annotated_candidates, flair_results
    )

    # Save this final candidate sentences dataframe (after dropping phrase list)
    final_annotated_candidates.drop("phrase_list").write_csv(
        "data/title_mentions_sent_results.csv"
    )

    final_annotated_candidates
    return (final_annotated_candidates,)


@app.cell(hide_code=True)
def _(mo, n_unmatched):
    mo.md(
        f"""
        ## Unmatched Annotations

        There are {n_unmatched} unmatched annotations. Six of these correspond to quotations without title mentions.
        """
    )
    return


@app.cell
def _(annotations, final_annotated_candidates, pl):
    unmatched_annos = annotations.filter(
        ~pl.col("anno_uuid").is_in(
            final_annotated_candidates.get_column("anno_uuid").to_list()
        )
    )
    unmatched_annos
    return (unmatched_annos,)


@app.cell
def _(mo, pl, unmatched_annos):
    fn_unmatched_annos = unmatched_annos.filter(
        (pl.col("anno_mentions_kapital") == "Yes")
        | (pl.col("anno_mentions_manifest") == "Yes")
    )

    mo.vstack(
        [
            mo.md(
                f"So, there are only {fn_unmatched_annos.shape[0]} annotations worth examining further (the ones with title mention annotations)."
            ),
            fn_unmatched_annos,
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
        ### OCR errors

        Three are missed due to OCR artifacts preventing proper lemmatization:

        - "...Kommunist im Sinne des kommunistischen **<u>Eanifests</u>** gewesen ist..."
        - " ...begann das Kommunistische **<u>Mauifest</u>** in den siebziger..."
        - "...war das Kommunistische **<u>Manifest¬</u>** von 1847..."

        The last one can be easily fixed by removing all "¬" characters which represent line continuations or OCR artifacts.
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ### Lemmatization errors

        The other two are caused by a declension inconsistently by stanza's lemmatizer: "des Kommunistischen **<u>manifestes</u>**". This phrase is sometimes incorrectly lemmatized by stanza as "der kommunistisch manifestes", so it is subsequntly missed in our searches since we expect the lemma "manifest".

        We can correct for this by also allowing "manifestes" or "Kommunistischen manifestes" as an additional search phrase.
        """
    )
    return


@app.cell(hide_code=True)
def _():
    ## Evaluating Lemmatization Search
    return


@app.cell
def _(chain, final_annotated_candidates, pl, title_phrases):
    # Construct a search phrase-centric dataframe of the annodated candidate data
    search_phrases_df = pl.DataFrame(
        chain(
            *[
                [
                    {"search_phrase": p, "title": title}
                    for p in title_phrases[title]
                ]
                for title in title_phrases
            ]
        )
    ).join_where(
        final_annotated_candidates,
        pl.col("search_phrase").is_in(pl.col("phrase_list")),
    )

    search_phrases_df.group_by(["search_phrase"]).agg(
        pl.col("title").first(),
        pl.len().alias("n_sents"),
        # Determine number of title candidates
        (
            pl.when(pl.col("title") == "Kapital")
            .then(pl.col("kapital_candidate"))
            .otherwise(pl.col("manifest_candidate"))
            .sum()
            .alias("n_title_candidates")
        ),
        # Determine number of yes title annotations
        (
            (
                pl.when(pl.col("title") == "Kapital")
                .then(pl.col("anno_mentions_kapital"))
                .otherwise(pl.col("anno_mentions_manifest"))
            )
            == "Yes"
        )
        .sum()
        .alias("n_title_anno_yes"),
        # Determine number of maybe title annotations
        (
            (
                pl.when(pl.col("title") == "Kapital")
                .then(pl.col("anno_mentions_kapital"))
                .otherwise(pl.col("anno_mentions_manifest"))
            )
            == "Maybe"
        )
        .sum()
        .alias("n_title_anno_maybe"),
        # Determine number of no title annotations
        (
            (
                pl.when(pl.col("title") == "Kapital")
                .then(pl.col("anno_mentions_kapital"))
                .otherwise(pl.col("anno_mentions_manifest"))
            )
            == "No"
        )
        .sum()
        .alias("n_title_anno_no"),
    ).sort(["title", "n_sents"], descending=True)
    return (search_phrases_df,)


@app.cell
def _(mo):
    mo.md(
        """
        ### Communist Manifesto

        **Manifest der Kommunistischen Partei.** This is a quite specific search phrase that only identifies a single candidate sentence. However, this sentence is a true title mention as confirmed by the manual annotation.

        **Kommunistische Manifest.** This search phrase is also specific but matches more sentences. The candidate sentences without title mention annotations are very likely to be missed title mentions. Is this the case?

        **Das Manifest.** This search phrase is not itself a *specific* title mention. Without further context, this phrase may not correspond to a title mention.

        **Manifest.** This search phrase is not itself a *specific* title mention. Without further context, this phrase may not correspond to a title mention.
        """
    )
    return


@app.cell
def _(pl, search_phrases_df):
    search_phrases_df.filter(
        pl.col("search_phrase") == "Kommunistische Manifest",
        pl.col("anno_mentions_manifest") == "No",
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ### Das Kapital

        How useful are these search phrases? How good are the sentences they match? What do they miss?
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ## Evaluating flair results
        For simplicity, we filter to the NER entities that contain the substring "band", "kapital", or "manifest" (case insensitive).
        """
    )
    return


@app.cell
def _(final_annotated_candidates, pl):
    final_annotated_candidates.group_by(
        ["anno_mentions_kapital", "anno_mentions_manifest"]
    ).agg(
        pl.col("flair_contains_band").sum(),
        pl.col("flair_contains_kapital").sum(),
        pl.col("flair_contains_manifest").sum(),
    )
    return


if __name__ == "__main__":
    app.run()
