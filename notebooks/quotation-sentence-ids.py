import marimo

__generated_with = "0.13.11"
app = marimo.App(width="medium")


@app.cell
def _():
    import pathlib

    import marimo as mo
    import polars as pl
    return mo, pathlib, pl


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # Quotation + Citation evaluation data

    Load annotations for quotations with documented citation and generate a data file in a format we can use for evaulation of sentence similarity / KNN methods (i.e., sentence ids for the two sentence corpora).
    """
    )
    return


@app.cell
def _(pl):
    quote_df = pl.read_csv("data/annotation_quotation_citations.csv")
    # annotation adjustment adapted from quote-data notebook in experiment 1
    # limit to the columns we care about
    quote_df = quote_df.select(
        pl.col("UUID", "FILE", "QUOTE_TRANSCRIPTION", "ANCHOR", "TAGS", "COMMENTS")
    )
    # turn char-offset into numeric start index, calculate end index
    quote_df = (
        quote_df.with_columns(
            start_index=pl.col("ANCHOR").str.slice(12).cast(dtype=int)
        )
        .with_columns(
            end_index=pl.col("start_index").add(
                pl.col("QUOTE_TRANSCRIPTION").str.len_chars()
            )
        )
        .drop("ANCHOR")
    )
    quote_df
    return (quote_df,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""Load sentence corpora for _Die Neue Zeit_ (DNZ) sample content.""")
    return


@app.cell
def _(pl):
    dnz_sent_df = pl.read_ndjson("data/sentence-corpora/dnz-sample-sents.jsonl")
    # calculate end character index
    dnz_sent_df = dnz_sent_df.with_columns(
        char_end_idx=pl.col("char_idx").add(pl.col("text").str.len_chars())
    )
    dnz_sent_df
    return (dnz_sent_df,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""Join DNZ sentences on quotation annotations by offset to find all sentences that overlap with a quotation."""
    )
    return


@app.cell
def _(dnz_sent_df, pl, quote_df):
    # join subset of quotes with page text; rename page text columns for clarity
    quote_sentences = quote_df.join_where(
        dnz_sent_df,
        # limit to annotations and sentences from the same file
        pl.col("FILE") == pl.col("file"),
        # look for sentences with any overlap with the annotation content
        pl.col("start_index") < pl.col("char_end_idx"),
        # annotation ends after sentence starts
        pl.col("end_index") > pl.col("char_idx"),
    )
    quote_sentences
    return (quote_sentences,)


@app.cell
def _(quote_sentences):
    # check the indices to confirm
    quote_sentences.select(
        "file", "start_index", "end_index", "char_idx", "char_end_idx"
    )
    return


@app.cell
def _(quote_sentences):
    # compare the text to confirm
    quote_sentences.select(
        "QUOTE_TRANSCRIPTION", "text", "start_index", "char_idx"
    )
    return


@app.cell
def _(quote_sentences):
    # select fields for output
    quote_sentences.select(
        "UUID", "file", "sent_id", "text", "COMMENTS"
    ).write_csv("data/sentence-eval-pairs/dnz_quoted_sentences.csv")

    quote_sentences.select("UUID", "file", "sent_id", "text", "COMMENTS")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    The citation data is in a human-readable form in the annotation notes.

    Output the quotation and the comment with citation information so citation text can be manually identified from MEGA xml.
    """
    )
    return


@app.cell
def _(mo, quote_df):
    content = []

    for row in quote_df.iter_rows(named=True):
        content.append(f"**# annotation id:** {row['UUID']}")
        content.append("> " + row["QUOTE_TRANSCRIPTION"])
        content.append(row["COMMENTS"])
        content.append("---")

    mo.md("\n\n".join(content))
    return


@app.cell
def _():
    # MEGA text content based on corrected citation page and line numbers

    # for each annotation above, store the filename and start and end strings that can be used to identify
    # indices in the text file, which can then be used to identify the set of overlapping sentences.

    mega_text = {
        # annotation id
        "4eb40d8e-928e-4b17-938f-8c72045db14d": {
            "file": "p395-396.txt",
            "start_str": "Ihr Erfolg bewies",
            "end_str": "Methode zur Produktion vollseitig entwickelter Menschen.",
        },
        "df81d5e4-4779-4117-b89c-7055c1cd7cc7": {
            "file": "p402.txt",
            "start_str": "daß die Zusammensetzung des kombinirten",
            "end_str": "Quelle humaner Entwicklung umschlagen muß",
        },
        "598859f7-3f49-4cb8-8383-8aefbc4ca667": {
            "file": "p25.txt",
            "start_str": "Die verschiednen Proportionen, worin",
            "end_str": "und scheinen ihnen daher durch das Herkommen \ngegeben",
        },
        "0f93adf5-75c6-49a9-a4ce-7caea83f636c": {
            "file": "p147.txt",
            "start_str": "Ist der Werth dieser Kraft höher",
            "end_str": "in verhältnißmäßig höheren Werthe",
        },
    }

    # text content here was manually extracted using the tei_page script with line numbers turned on and footnotes omitted,
    # then manually selecting from the specified lines based on the quotation text above

    # this is the full set of text content used to generate start and end strings above;
    # no longer directly used, but kept as a reference

    mega_text2 = {
        # ./src/remarx/tei_page.py data/MEGA_A2_B005-00_ETX.xml -s 395 -e 397 --no-footnotes
        # data/mega-sample-pages/p395-396.txt
        "4eb40d8e-928e-4b17-938f-8c72045db14d": """Ihr Erfolg bewies zuerst die Möglichkeit der Verbindung von
    Unterricht und Gymnastik mit Handarbeit, also auch von Handarbeit mit 
    Unterricht und Gymnastik. Die Fabrikinspektoren entdeckten bald aus den
    Zeugenverhören der Schulmeister, daß die Fabrikkinder, obgleich sie nur
    halb so viel Unterricht genießen als die regelmäßigen Tagesschüler, eben so
    viel und oft mehr lernen. „Die Sache ist einfach. Diejenigen, die sich nur
    einen halben Tag in der Schule aufhalten, sind stets frisch und fast immer
    fähig und willig Unterricht zu empfangen. Das System halber Arbeit und
    halber Schule macht jede der beiden Beschäftigungen zur Ausruhung und
    Erholung von der andern und folglich viel angemeßner für das Kind als die
    ununterbrochne Fortdauer einer von beiden. Ein Junge, der von Morgens
    früh in der Schule sitzt, und nun gar bei heißem Wetter, kann unmöglich mit
    einem andern wetteifern, der munter und aufgeweckt von seiner Arbeit
    kommt“. Weitere Belege findet man in Senior's   Rede auf dem
    sociologischen Kongress zu Edinburg 1863. Er zeigt hier auch u. a. nach, wie
    der einseitige, unproduktive und verlängerte Schultag der Kinder der hö-
    heren und mittleren Klassen die Arbeit der Lehrer nutzlos vermehrt,
    „während er Zeit, Gesundheit und Energie der Kinder nicht nur fruchtlos,
    sondern absolut schädlich verwüstet“. Aus dem Fabriksystem, wie man
    in Detail bei Robert Owen verfolgen kann, entsproß der Keim der Erziehung
    der Zukunft, welche für alle Kinder über einem gewissen Alter produktive
    Arbeit mit Unterricht und Gymnastik verbinden wird, nicht nur als eine
    Methode zur Steigerung der gesellschaftlichen Produktion, sondern als die
    einzige Methode zur Produktion vollseitig entwickelter Menschen.
        """,
        # data/mega-sample-pages/p402.txt
        "df81d5e4-4779-4117-b89c-7055c1cd7cc7": """daß die Zusammensetzung des kombinirten Arbeitspersonals aus Individuen
    beiderlei Geschlechts und der verschiedensten Altersstufen, obgleich in ihrer
    naturwüchsig brutalen, kapitalistischen Form, wo der Arbeiter für den Pro-
    duktionsprozeß, nicht der Produktionsprozeß für den Arbeiter da ist, Pest-
    quelle des Verderbs und der Sklaverei, unter entsprechenden Verhältnissen
    umgekehrt zur Quelle humaner Entwicklung umschlagen muß.""",
        # data/mega-sample-pages/p25.txt
        "598859f7-3f49-4cb8-8383-8aefbc4ca667": """Die verschiednen Proportionen, worin
    verschiedne Arbeitsarten auf einfache Arbeit als ihre Maßeinheit reducirt
    sind, werden durch einen gesellschaftlichen Prozeß hinter dem Rücken der
    Produzenten festgesetzt und scheinen ihnen daher durch das Herkommen
    gegeben.""",
        # data/mega-sample-pages/p147.txt
        "0f93adf5-75c6-49a9-a4ce-7caea83f636c": """Ist der Werth dieser Kraft höher,
    so äußert sie sich aber auch in höherer Arbeit und vergegenständlicht sich
    daher, in denselben Zeiträumen, in verhältnißmäßig höheren Werthen.
    """,
    }
    return (mega_text,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""Use filenames and start/end strings to determine character indices, for matching with sentences."""
    )
    return


@app.cell
def _(mega_text, pathlib, pl):
    mega_page_dir = pathlib.Path("data/mega-sample-pages/")

    cited_text_info = []


    for annotation_id, citation_source in mega_text.items():
        file_path = mega_page_dir / citation_source["file"]
        file_contents = file_path.read_text()
        start_index = file_contents.index(citation_source["start_str"])
        end_index = file_contents.index(citation_source["end_str"]) + len(
            citation_source["end_str"]
        )
        cited_text_info.append(
            {
                "annotation_id": annotation_id,
                "file": citation_source["file"],
                "start_idx": start_index,
                "end_idx": end_index,
            }
        )

    cited_texts_df = pl.from_dicts(cited_text_info)
    cited_texts_df
    return (cited_texts_df,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""Load sentence corpus file.""")
    return


@app.cell
def _(pl):
    mega_sent_df = pl.read_ndjson("data/sentence-corpora/mega-sample-sents.jsonl")

    # calculate end character index
    mega_sent_df = mega_sent_df.with_columns(
        char_end_idx=pl.col("char_idx").add(pl.col("text").str.len_chars())
    )
    mega_sent_df
    return (mega_sent_df,)


@app.cell
def _(cited_texts_df, mega_sent_df, pl):
    # join sentence corpus with cited sentence details

    # join subset of quotes with page text; rename page text columns for clarity
    cited_sentences = cited_texts_df.join_where(
        mega_sent_df,
        # limit to annotations and sentences from the same file
        pl.col("file") == pl.col("file_right"),
        # look for sentences with any overlap with the annotation content
        pl.col("start_idx") < pl.col("char_end_idx"),
        # annotation ends after sentence starts
        pl.col("end_idx") > pl.col("char_idx"),
    ).select("annotation_id", "file", "sent_id", "text")

    cited_sentences.write_csv("data/sentence-eval-pairs/marx_cited_sentences.csv")
    cited_sentences
    return


@app.cell
def _(mo):
    mo.md(
        r"""
    ### next steps:

    - manually match up dnz <-> mega sentence pairs (first-pass, easy for single-sentence quotes)
    - share with project team for review/refinement as google spreadsheet
    """
    )
    return


if __name__ == "__main__":
    app.run()
