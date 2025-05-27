

import marimo

__generated_with = "0.13.2"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import polars as pl
    from itertools import chain

    from remarx.polar_utils import load_flair_ner, load_title_annotations, load_title_phrases
    return load_flair_ner, load_title_annotations, mo, pl


@app.cell
def _():
    # Experiment II: Title Mentions Demo
    return


@app.cell(hide_code=True)
def _():
    ## Setup
    return


@app.cell
def _(pl):
    # Load candidate sentences with annotation and flair data
    candidate_sents = pl.read_csv("data/title_mentions_sent_results.csv")
    candidate_sents
    return (candidate_sents,)


@app.cell
def _(load_title_annotations):
    # Load manual annotation data
    annotations = load_title_annotations()
    annotations
    return (annotations,)


@app.cell
def _(load_flair_ner):
    # Load flair data
    ner_data = load_flair_ner()
    ner_data
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
        ## Lemmatized Search

        First, we try a simple (case-insensitive) lemmatized search to identify sentences with title mentions.
        """
    )
    return


@app.cell(hide_code=True)
def _(mo, pl):
    title_phrases_df = pl.read_csv("data/title_searchphrases.csv").sort(["title", "phrase"])
    mo.vstack(
        [
            mo.md("We use the following search phrases for Kapital and the Communist Manifesto:"),
            title_phrases_df,
        ]
    )
    return (title_phrases_df,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""The search works as follows: First, we lemmatize our search phrases and we split our documents into sentences. Then, we lemmatize each sentence and check which lemmatized search phrases (if any) are occur within the sentence.""")
    return


@app.cell(hide_code=True)
def _(mo, pl, title_phrases_df):
    mo.vstack([
            mo.md("So, our search phrases will have the following lemmatized forms:"),
            title_phrases_df.with_columns(pl.Series(
                ["band", "der kapital", "erst band", "erst band der kapital", "kapital", "der manifest",
                "kommunistisch manifest", "manifest", "manifest der kommunistisch partei", "manifesto"]
            ).alias("lemmatized_phrases")),
            mo.md("""
            Note that some of these search phrases will contain others. For example, any sentence that matches on "Kommunistische Manifest" will also be a match for "Manifest"
            """),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
        Let's illustrate the search process with the following sentence:

        > Man merkt jetzt, weshalb Herr Platter aus allen möglichen Schriften von Marx, vom Kommunistischen manifest bis zum dritten Bande des „Kapital“, alle mög¬ lichen Zitate herauschleppt, aber um die Literatur der Internationalen in weitem Bogen herumgeht.

        This will sentence will have the following lemmatized form. Note that we remove all punctuation as determined by the part-of-speech tagger.

        > man merken jetzt weshalb Herr Platter aus alle möglich Schrift von Marx von <u>**der kommunistisch manifest**</u> bis zu der dritt Bande <u>**der Kapital**</u> alle mög¬en lich Zitat herauschleppen aber um der Literatur der international in weit Bogen herumgehen

        This sentence has the following search phrase matches for each title:

        - Das Kapital: "Kapital", "Das Kapital"
        - Communist Manifesto: "Manifest", "Kommunistische Manifest"

        Note thate "Bande" is not captured because this lemmatizes to "bande" and not "band". This suggests there might be some additional or alternative search phrases worth considering.
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""### Unmatched Annotations""")
    return


@app.cell(hide_code=True)
def _(annotations, candidate_sents, mo, pl):
    # get number of unmatched annotations
    n_unmatched = annotations.filter(
        ~pl.col("anno_uuid").is_in(
            candidate_sents.get_column("anno_uuid").to_list()
        )
    ).shape[0]

    mo.md(
        f"""
        There are {n_unmatched} unmatched annotations. Six of these correspond to quotations without title mentions.
        """
    )
    return


@app.cell(hide_code=True)
def _(annotations, candidate_sents, mo, pl):
    unmatched_annos = annotations.filter(
        ~pl.col("anno_uuid").is_in(
            candidate_sents.get_column("anno_uuid").to_list()
        )
    )

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
        #### OCR errors

        Three are missed due to OCR artifacts preventing proper lemmatization:

        - "...Kommunist im Sinne des kommunistischen **<u>Eanifests</u>** gewesen ist..."
        - " ...begann das Kommunistische **<u>Mauifest</u>** in den siebziger..."
        - "...war das Kommunistische **<u>Manifest¬</u>** von 1847..."

        The last one can be easily fixed by removing all "¬" characters which represent line continuations or OCR artifacts.
        """
    )
    return


app._unparsable_cell(
    r"""
    #### Lemmatization errors

    The other two are caused by a declension inconsistently by stanza's lemmatizer: \"des Kommunistischen **<u>manifestes</u>**\". This phrase is sometimes incorrectly lemmatized by stanza as \"der kommunistisch manifestes\", so it is subsequntly missed in our searches since we expect the lemma \"manifest\".

    We can correct for this by also allowing \"manifestes\" or \"Kommunistischen manifestes\" as an additional search phrase.
    """,
    column=None, disabled=False, hide_code=True, name="_"
)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
        ### Matched Sentences

        Now, we can do some cursory views of the matched sentences which we call candidate sentences since we generally consider these to be sentences where we anticipate title mentions may occur.
        """
    )
    return


@app.cell
def _(pl):
    pl.read_csv("data/search_stats.csv")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""Our lemmatized search finds many more sentences than were manually annotated. We might expect that some quotation matches may also contain title mentions, thus we have a "maybe" annotation column for each title.""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
        ## Named Entity Recognition
        An alternative approach is to perform named entity recognition (NER) in hopes of finding titles. However, the NER models available for langugaes other than English are fairly limited. This is generally due to the more limited training data which have the following NER tags:

        - **PER:** Person
        - **LOC:** Location
        - **ORG:** Organization
        - **MISC:** Miscellaneous 
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
        We found that in some cases NER could identify mispelled titles. For example,

        > Sie erklären die Thatsache, daß Lassalle, unbeschadet der juristischen und philosophischen Form, in welche er oft nur erst den ökonomischen Inhalt zu schlagen wußte, Kommunist im Sinne des kommunistischen **<u>Eanifests</u>** gewesen ist, für eine bös¬ willige Erfindung der Marxisten und machen Lassalle zu einem Bundesbruder von Rodbertus.

        "Eanifests" is identified as a MISC entity. It's not as good as identifyin the full "komministischence Eanifests" but it's closer.
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
        It seems to be better at identifying titles when they are in quotes such as

        > Seit dem Erscheinen des dritten Bandes „**<u>Kapital</u>**" kann über die Nothwendigkeit, in diesem Punkte Klarheit zu schaffen, kein Zweifel mehr bestehen.
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""We run NER on all candidate sentences and for simplicity filter to entities that contain the substring "band", "kapital", or "manifest" (case insensitive). We can see an overview of the results in the following table:""")
    return


@app.cell(hide_code=True)
def _(candidate_sents, pl):
    candidate_sents.group_by(
        ["anno_mentions_kapital", "anno_mentions_manifest"]
    ).agg(
        pl.col("flair_contains_band").sum(),
        pl.col("flair_contains_kapital").sum(),
        pl.col("flair_contains_manifest").sum(),
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
        ## Compiled Results

        The results of the candidate sentences have been compiled into a single table and have been uploaded to the Project Google Drive folder within Experiment II as `title_mentions_sents_results.csv`.
        """
    )
    return


@app.cell
def _(candidate_sents):
    candidate_sents
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
