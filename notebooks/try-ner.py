

import marimo

__generated_with = "0.13.3"
app = marimo.App(width="medium")


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

    nlp_de = stanza.Pipeline("de", processors="tokenize,mwt,lemma,ner")
    return nlp_de, stanza


@app.cell
def _():
    # example sentence from the title mentions subset data
    sample1 = """Wie alles, was wir von Marx aus¬ jener Zeit besitzen, wie auch das „Kommunistische Manifest", zeigt seine Rede¬ über den Freihandel nur die gewaltigen äußeren Umrisse des Gebäudes, der innere Aufbau fehlt noch. Engels konnte sich 1888 schon auf die zwei ersten Bände des „Kapital" und noch vieles Andere stützen, doch fehlie der dritte, Band mit seinen wichtigen Untersuchungen über die Profitbildung, die Grund¬ rente und den Preis, die für die Lehre von der Konkurrenz und damit auch für die Beurtheilung der Handelspolitik unentbehrlich sind."""
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
        ent_table = mo.ui.table(data=entity_data, pagination=True, selection=None)
        return mo.vstack([text, ent_table])
    return (show_stanza_entities,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""The first example sentence only identifies Marx and Engels as person entities, does not identify any titles.""")
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
def _(stanza):
    # try the same thing in English, for comparison...

    nlp_en = stanza.Pipeline("en", processors="tokenize,mwt,lemma,ner")
    return (nlp_en,)


@app.cell
def _(nlp_en, sample1_en, show_stanza_entities):
    doc1_en = nlp_en(sample1_en)
    show_stanza_entities(sample1_en, doc1_en)
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
                # weirdly can't figure out a good way to get the text from the label;
                # unidentified label looks like this:  Span[6:7]: "Marx"
                "Text": label.unlabeled_identifier.rsplit(":", 1)[-1]
                .strip()
                .strip('"'),
                "Entity Type": label.value,
                "Confidence": label.score,
            }
            for label in sentence.get_labels(label_type="ner")
        ]
        ent_table = mo.ui.table(data=entity_data, pagination=True, selection=None)
        return mo.vstack([text, ent_table])
    return (show_flair_entities,)


@app.cell
def _(sample1, show_flair_entities):
    show_flair_entities(sample1)
    return


@app.cell
def _(sample2, show_flair_entities):
    show_flair_entities(sample2)
    return


if __name__ == "__main__":
    app.run()
