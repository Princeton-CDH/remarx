

import marimo

__generated_with = "0.13.3"
app = marimo.App(width="medium", app_title="Try Stanza + Flair NER for titles")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""# Compare Stanza/Flair NER for titles""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ## Stanza

        Stanza German NER classifier only supports 4 types. The only that might work for titles `MISC` entity tag. Does this pick up any of our titles?
        """
    )
    return


@app.cell
def _():
    import stanza
    from stanza.pipeline.core import DownloadMethod

    nlp_de = stanza.Pipeline(
        "de",
        processors="tokenize,mwt,ner",
        download_method=DownloadMethod.REUSE_RESOURCES,
    )
    return DownloadMethod, nlp_de, stanza


@app.cell
def _():
    # example sentence from the title mentions subset data
    sample1 = """Wie alles, was wir von Marx aus¬ jener Zeit besitzen, wie auch das „Kommunistische Manifest", zeigt seine Rede¬ über den Freihandel nur die gewaltigen äußeren Umrisse des Gebäudes, der innere Aufbau fehlt noch. Engels konnte sich 1888 schon auf die zwei ersten Bände des „Kapital" und noch vieles Andere stützen, doch fehlie der dritte, Band mit seinen wichtigen Untersuchungen über die Profitbildung, die Grund¬ rente und den Preis, die für die Lehre von der Konkurrenz und damit auch für die Beurtheilung der Handelspolitik unentbehrlich sind."""
    sample1_expected_titles = [
        '„Kommunistische Manifest"',
    ]

    # english translation of the above, generated with google translate
    sample1_en = """Like everything we possess from Marx from that period, including the "Communist Manifesto," his speech on free trade shows only the massive outer outlines of the building; the inner structure is still missing. In 1888, Engels could already rely on the first two volumes of "Capital" and much else besides, but the third volume, with its important investigations into profit formation, ground rent, and price—which are indispensable for the theory of competition and thus also for the evaluation of trade policy—was missing."""

    sample2 = """Sie hatten schon im „Kommuni¬ stischen Manifest" erklürt, daß die Arbetterklasse unweigerlich die Bourgevisie, zu unterstützen habe, sobald und soweit diese ernsthaft mit dem Absolutismus und dem Feudalismus anbinde, und sie hatten nach diesem Grundsatz währende der Revolutionsjahre gehandelt, aber sie meinten, daß man die absolutistisch¬ feudale Reaktion nicht wirkungsloser bekämpfen könne als unter der Finte eines allgemeinen Harmoniedusels zwischen Bourgepisie und Proletariat."""
    return sample1, sample1_en, sample2


@app.cell
def _(nlp_de, sample1):
    doc1 = nlp_de(sample1)  # run annotation over a sentence
    return (doc1,)


@app.cell
def _(mo):
    # define a method to display a sentence tagged with stanza nlp and the entities found
    def show_stanza_entities(text, nlpdoc):
        entity_data = [
            {"Text": ent.text, "Entity Type": ent.type} for ent in nlpdoc.ents
        ]
        ent_table = mo.ui.table(
            data=entity_data, pagination=False, selection=None, show_download=False
        )
        # use start/end character indices to highlight entities in the sentence
        output_text = []
        prev_start = 0
        for ent in nlpdoc.ents:
            output_text.append(text[prev_start : ent.start_char])
            output_text.append(f"<mark>{ent.text}</mark>")
            prev_start = ent.end_char
        # add any remaining text after the last entity
        output_text.append(text[prev_start:])
        # for ent in nlpdocs.ents
        return mo.vstack([mo.md("".join(output_text)), ent_table])
    return (show_stanza_entities,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        The first example sentence only identifies Marx and Engels as person entities, does not identify any titles.
        This passage mentions both Communist Manifesto and Das Kapital.
        """
    )
    return


@app.cell
def _(doc1, sample1, show_stanza_entities):
    show_stanza_entities(sample1, doc1)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""In the second example sentence, one of our titles is picked up, in spite of the fact that it includes a line break and our weird continuation character.""")
    return


@app.cell
def _(nlp_de, sample2, show_stanza_entities):
    show_stanza_entities(sample2, nlp_de(sample2))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        Just for comparison, I used Google Translate on the first sentence and ran Stanza English NER. This is a different model with a much larger number of entities; it picks up Communist Manifesto as a "Work of Art."
        """
    )
    return


@app.cell
def _(DownloadMethod, stanza):
    # try the same thing in English, for comparison...

    nlp_en = stanza.Pipeline(
        "en",
        processors="tokenize,mwt,ner",
        download_method=DownloadMethod.REUSE_RESOURCES,
    )
    return (nlp_en,)


@app.cell
def _(nlp_en, sample1_en, show_stanza_entities):
    doc1_en = nlp_en(sample1_en)
    show_stanza_entities(sample1_en, doc1_en)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""### Test Stanza NER on title mention subset data""")
    return


@app.cell
def _():
    import polars as pl

    title_mention_subset = pl.read_csv("data/title_mentions_subset.csv")
    title_mention_subset.select(pl.col("Text"), pl.col("Marx Title Mentions"))
    return pl, title_mention_subset


@app.cell
def _(nlp_de):
    # generate a delimited string of the text of all entities tagged as "MISC"
    def stanza_get_possible_titles(text):
        processed_text = nlp_de(text)  # run annotation over a sentence
        return " | ".join(
            [ent.text for ent in processed_text.ents if ent.type == "MISC"]
        )
    return (stanza_get_possible_titles,)


@app.cell
def _(pl, stanza_get_possible_titles, title_mention_subset):
    # get possible titles from stanza
    title_mention_subset_ner = title_mention_subset.with_columns(
        pl.col("Text")
        .map_elements(stanza_get_possible_titles, return_dtype=pl.String)
        .alias("stanza")
    )
    return (title_mention_subset_ner,)


@app.cell
def _(pl, title_mention_subset_ner):
    # filter to those that had any misc entities found
    stanza_misc_ents = title_mention_subset_ner.filter(pl.col("stanza").ne(""))
    return (stanza_misc_ents,)


@app.cell(hide_code=True)
def _(mo, stanza_misc_ents, title_mention_subset):
    mo.md(
        f"""
        ### Title candidates from Stanza NER

        Of the {title_mention_subset.height} rows in the title mention subset, only {stanza_misc_ents.height} have 'MISC' entities identified by Stanza German NER.
        """
    )
    return


@app.cell
def _(pl, stanza_misc_ents):
    stanza_misc_ents.select(
        pl.col("Text"), pl.col("Marx Title Mentions"), pl.col("stanza")
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ### Title mentions missed by Stanza NER

        Here are the rows from the title mentions subset that don't have any MISC entity annotations identified by Stanza.  Unclear yet if there's any pattern why these are not found but the others are.
        """
    )
    return


@app.cell
def _(pl, title_mention_subset_ner):
    # filter to those that had no misc entities found, show only text and expected titles
    title_mention_subset_ner.filter(pl.col("stanza").eq("")).select(
        pl.col("Text"), pl.col("Marx Title Mentions")
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ## Flair

        Run the same two sample text passages through Flair German NER model.

        This one is picking up at least some of our titles under the MISC tag.
        """
    )
    return


@app.cell
def _():
    from flair.data import Sentence
    from flair.nn import Classifier
    from flair.splitter import SegtokSentenceSplitter

    # initialize sentence splitter
    splitter = SegtokSentenceSplitter()

    # load one of the German NER models
    # options: de-ner, de-ner-large, de-ler (legal entities)
    tagger = Classifier.load("de-ner-large")


    # NOTE: This sample text is actually multiple sentences;
    # Could use splitter to split text into a list of sentences;
    # it doesn't seem to impact results in this case.
    # sentences_sample1 = splitter.split(sample1)
    # tagger.predict(sentences_sample1)
    return Sentence, tagger


@app.cell
def _(Sentence, mo, tagger):
    # equivalent of method above, but for flair sentences and labels
    def show_flair_entities(text):
        # make a sentence from the text
        sentence = Sentence(text, language_code="de")
        # run NER over sentence
        tagger.predict(sentence)
        entity_data = [
            {
                "Text": span.text,
                "Entity Type": span.tag,  # tag = shortcut to value of the first label
                "Confidence": span.labels[0].score,
            }
            for span in sentence.get_spans(label_type="ner")
        ]

        ent_table = mo.ui.table(
            data=entity_data, pagination=False, selection=None, show_download=False
        )

        # use span start/end character indices to highlight entities in the sentence
        output_text = []
        prev_start = 0
        for span in sentence.get_spans(label_type="ner"):
            output_text.append(text[prev_start : span.start_position])
            output_text.append(f"<mark>{span.text}</mark>")
            prev_start = span.end_position
        # add any remaining text after the last entity
        output_text.append(text[prev_start:])
        # for ent in nlpdocs.ents
        return mo.vstack([mo.md("".join(output_text)), ent_table])
    return (show_flair_entities,)


@app.cell
def _(sample1, show_flair_entities):
    show_flair_entities(sample1)
    return


@app.cell
def _(sample2, show_flair_entities):
    show_flair_entities(sample2)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""### Test Flair NER on title mention subset data""")
    return


@app.cell
def _(Sentence, tagger):
    # generate a delimited string of the text of all entities tagged as "MISC"
    def flair_get_possible_titles(text):
        # make a sentence from the text
        sentence = Sentence(text, language_code="de")
        # run NER over sentence
        tagger.predict(sentence)
        return " | ".join(
            [
                span.text
                for span in sentence.get_spans(label_type="ner")
                if span.tag == "MISC"
            ]
        )
    return (flair_get_possible_titles,)


@app.cell
def _(flair_get_possible_titles, pl, title_mention_subset_ner):
    # get possible titles from flair
    title_mention_subset_ner_both = title_mention_subset_ner.with_columns(
        pl.col("Text")
        .map_elements(flair_get_possible_titles, return_dtype=pl.String)
        .alias("flair")
    )
    return (title_mention_subset_ner_both,)


@app.cell
def _(pl, title_mention_subset_ner_both):
    flair_misc_ents = title_mention_subset_ner_both.filter(pl.col("flair").ne(""))
    return (flair_misc_ents,)


@app.cell(hide_code=True)
def _(flair_misc_ents, mo, title_mention_subset):
    mo.md(
        f"""
        ### Title candidates from Flair NER

        Of the {title_mention_subset.height} rows in the title mention subset, {flair_misc_ents.height} have 'MISC' entities identified by Flair German NER.
        """
    )
    return


@app.cell
def _(flair_misc_ents, pl):
    flair_misc_ents.select(
        pl.col("Text"),
        pl.col("Marx Title Mentions"),
        pl.col("flair"),
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""Do Stanza and Flair identify the same things, where they overlap?""")
    return


@app.cell
def _(flair_misc_ents, pl):
    flair_misc_ents.select(
        pl.col("Marx Title Mentions"),
        pl.col("flair"),
        pl.col("stanza"),
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ### Title mentions missed by Flair NER

        Here are the rows from the title mentions subset that don't have any MISC entity annotations identified by Flair.  Unclear if there's any pattern why these are not found but the others are.
        """
    )
    return


@app.cell
def _(pl, title_mention_subset_ner_both):
    # filter to those that had no misc entities found, show only text and expected titles
    title_mention_subset_ner_both.filter(pl.col("flair").eq("")).select(
        pl.col("Text"), pl.col("Marx Title Mentions")
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        In at least a few cases, titles (Kapital and Die Neue Zeit) are being tagged with other NER tags.
        So, let's run flair again and capture all identified NER entities for all the title mention subset data, and save for later reference/comparison.
        """
    )
    return


@app.cell
def _(Sentence, tagger):
    # get all NER entities returned by flair
    # return as a dict keyed on entity type, value is a delimited string of entity text
    def flair_get_entities(text):
        # make a sentence from the text
        sentence = Sentence(text, language_code="de")
        # run NER over sentence
        tagger.predict(sentence)

        entities = {"PER": [], "ORG": [], "MISC": [], "LOC": []}

        for span in sentence.get_spans(label_type="ner"):
            entities[span.tag].append(span.text)
        return {tag: " | ".join(text) for tag, text in entities.items()}
    return (flair_get_entities,)


@app.cell
def _(flair_get_entities, pl, title_mention_subset):
    # get all entities and then unnest them so we get a column for each entity type
    title_mention_flair_ner = title_mention_subset.with_columns(
        pl.col("Text")
        .map_elements(flair_get_entities, return_dtype=pl.Struct)
        .alias("result")
    ).unnest("result")
    title_mention_flair_ner
    return (title_mention_flair_ner,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""A few records have titles (_Kapital_, _Die Neue Zeit_) that are getting annotated as **ORG** entities rather than **MISC**.""")
    return


@app.cell
def _(pl, title_mention_flair_ner):
    # filter to the rows with known titles in the ORG entity list
    title_mention_flair_ner.filter(
        pl.col("ORG").str.contains("Kapital") | pl.col("ORG").str.contains("Zeit")
    ).select(
        pl.col("Text"),
        pl.col("Tags"),
        pl.col("Marx Title Mentions"),
        pl.col("ORG"),
    )
    return


@app.cell
def _(pl, title_mention_flair_ner):
    # save flair NER results for title mentions subset data, for later reference;
    # only create the output file if it doesn't already exist

    import pathlib

    # select columns for output and save
    flair_ner_output = (
        title_mention_flair_ner.select(
            pl.col("UUID"),
            pl.col("PER"),
            pl.col("ORG"),
            pl.col("MISC"),
            pl.col("LOC"),
        )
        .with_columns(ner_model=pl.lit("de-ner-large"))
        # replace empty strings with None for cleaner CSV output
        .with_columns(pl.col(pl.String).replace("", None))
    )

    output_file = pathlib.Path("data/title_mentions_flair_ner.csv")
    if not output_file.exists():
        flair_ner_output.write_csv(output_file)
    return


if __name__ == "__main__":
    app.run()
