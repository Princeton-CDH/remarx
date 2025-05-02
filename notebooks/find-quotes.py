

import marimo

__generated_with = "0.13.2"
app = marimo.App(width="medium", app_title="Finding General Quotes")


@app.cell
def _():
    import marimo as mo
    import polars as pl
    import re
    return mo, pl, re


@app.cell
def _(mo):
    mo.md(
        """
        # Finding general quotes in Die Neue Zeit
        This notebook explores finding quotes within Die Neue Zeit article using simple search rules.
        Namely, that a quote is text that occurs between the starting quote character „ and an ending quote character (either “ or ").
        In practice, this identifies quotations as well as titles and concepts.

        **Findings:** This simple approach works when the underlying transcription is accurate and when quotations are not broken across pages. The latter is especially a problem for block quotes.
        """
    )
    return


@app.cell
def _(re):
    def find_quotes(text):
        search_text = text
        results = []
        # Find basic quotes of the form „ ... “ or „ ... "
        for match in re.finditer(r"„[^“\"]+[“\"]", search_text):
            # Add match to results
            results.append(match)
            ## White out match
            start, end = match.span()
            search_text = (
                search_text[:start] + " " * (end - start) + search_text[end:]
            )
        return results
    return (find_quotes,)


@app.cell
def _():
    ## Load quotes and page data
    return


@app.cell
def _(pl):
    # Load quotes data
    quotes_data = pl.read_csv("data/direct_quotes_subset.csv")
    quotes_data.select(
        "FILE", "page_index", "TAGS", "QUOTE_TRANSCRIPTION", "start_index"
    ).sort("page_index", "start_index")
    return (quotes_data,)


@app.cell
def _(quotes_data):
    # Convert quote data into page data
    page_data = (
        quotes_data.unique("page_text")
        .select("FILE", "page_index", "page_text")
        .sort("page_index")
    )
    page_data
    return (page_data,)


@app.cell
def _(mo):
    mo.md(r"""## View Results by Page""")
    return


@app.cell
def _(mo, page_data):
    page_slider = mo.ui.slider(start=1, stop=len(page_data.rows()), value=2)
    return (page_slider,)


@app.cell
def _(mo, page_slider):
    mo.vstack(
        [
            mo.md("Select Slider:"),
            page_slider,
            mo.md(f"Selected Page: {page_slider.value}"),
        ]
    )
    return


@app.cell
def _():
    # Store notes for pages (index by page id)
    notes = {
        18: """- Corresponds to page 25""",
        38: """- Corresponds to page 43\n- Missing leading quote mark: "Frage an:\n<mark>**„**</mark>Bet gewissem"\n- Spurious quote mark: "die Naturprodukte nicht!<mark>**"**</mark> Hier"
        """,
        76: """- Corresponds to page 76\n- Missing ending quote mark, transcribed as period: "und Schön¬
    geister<mark>**.**</mark>\n— heißt es\n- Missing ending quote mark: "die Verwirklichung der Philssophie<mark>**“**</mark> (a. a. O. S. 85)."
    """,
        256: """- Corresponds to page 231""",
        301: """- Corresponds to page 268\n- Ending block quote not captured because it continues to the next page: "„Die Kommunisten [...]"
        """,
        499: """- Corresponds to page 289""",
        545: """- Corresponds to page 493\n- Missing ending quote, transcribed as ¬: "die „Heilige Familie<mark>**¬**</mark> zurück"
        """,
        546: """- Corresponds to page 494\n- Spurious quote mark: "Produktionsprozesse\nleitet,<mark>**“**</mark> wiedergefunden"
        """,
        549: """- Corresponds to page 497\n- Potentially incorrect annotations. Does this page contain any direct quotations from Kapital, or are there just citations (e.g., the footnote)? - The text seems to be missing the closing quotation for a referenced title. As a result, several title mentions are grouped together.""",
        661: """- Corresponds to page 612""",
    }
    return (notes,)


@app.cell
def _(find_quotes, mo, notes, page_data, page_slider):
    row_id = page_slider.value - 1
    page_id = page_data.row(row_id)[1]
    page_text = page_data.row(row_id)[2]
    results = [mo.md(f"## Page {page_id}")]
    if page_id in notes:
        results.append(mo.md(f"### Notes\n{notes[page_id]}"))
    # Get matches
    matches = find_quotes(page_text)
    # Highlight (and bold) Page Text
    highlighted_page = page_text
    for match in sorted(matches, reverse=True, key=lambda x: x.span()):
        start, end = match.span()
        highlighted_page = (
            highlighted_page[:start]
            + "<mark>**"
            + highlighted_page[start:end]
            + "</mark>**"
            + highlighted_page[end:]
        )
    results.append(mo.md(f"### Page with Quotes Highlighted\n{highlighted_page}"))
    # Print raw page
    print("Raw Page Text:\n" + page_text)
    mo.vstack(results)
    return


if __name__ == "__main__":
    app.run()
