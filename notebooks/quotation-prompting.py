import marimo

__generated_with = "0.12.10"
app = marimo.App(
    width="full",
    app_title="Quotation prompt demo",
    css_file="highlight.css",
)


@app.cell
def _():
    import marimo as mo
    import polars as pl

    from remarx.sandbox_utils import submit_prompt, get_text_response
    from remarx.notebook_utils import (
        highlight_bracketed_text,
        compare_highlighted_texts,
        highlight_sidebyside,
        html_diff,
        texts_differ,
    )
    return (
        compare_highlighted_texts,
        get_text_response,
        highlight_bracketed_text,
        highlight_sidebyside,
        html_diff,
        mo,
        pl,
        submit_prompt,
        texts_differ,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        # Test quotation detection prompts

        This notebook tests the quotation detection prompt templates; it is inspired by the title mentions notebook.
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ## Load quotation subset data

        Choose 2-3 pages to test with; at least one should have two quotes.
        """
    )
    return


@app.cell
def _(pl):
    quotes_df = pl.read_csv("data/subset/direct_quotes.csv")
    quotes_df.group_by("page_index").agg(pl.col("UUID").count()).head()
    return (quotes_df,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""Page index 661 has two quotes; page index 256 has one.""")
    return


@app.cell
def _(pl, quotes_df):
    test_quotes = quotes_df.filter(pl.col("page_index").is_in([661, 256]))

    # order by start index within the text
    test_quotes = test_quotes.sort("start_index")

    test_quotes
    return (test_quotes,)


@app.cell
def _(test_quotes):
    # just three rows, so get as a list of dict
    rows = list(test_quotes.iter_rows(named=True))

    # grab the page text content
    page_text_i256 = rows[0]["page_text"]

    page_text_i661 = rows[1]["page_text"]
    return page_text_i256, page_text_i661, rows


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        Highlight annotation for page 256.

        The annotation highlights a long, multiline passage at the end of the page.
        """
    )
    return


@app.cell
def highlight_text():
    def highlight_text(text, start_index, end_index):
        text_before = text[:start_index]
        highlight_text = text[start_index:end_index]
        text_after = text[end_index:]
        return f"{text_before}[{highlight_text}]{text_after}"
    return (highlight_text,)


@app.cell
def _(highlight_bracketed_text, highlight_text, page_text_i256, rows):
    # start index in the annotation data is from beginning of file;
    # adjust by start of page

    page_i256_start = rows[0]["page_start"]
    # add brackets for annotation data so highlights can be compared
    page_text_i256_annotated = highlight_text(
        page_text_i256,
        rows[0]["start_index"] - page_i256_start,
        rows[0]["end_index"] - page_i256_start,
    )

    highlight_bracketed_text(page_text_i256_annotated)
    return page_i256_start, page_text_i256_annotated


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""Highlight annotations for page 661, which has two quotes. One quote comes directly after the other.""")
    return


@app.cell
def _(highlight_bracketed_text, highlight_text, page_text_i661, rows):
    page_i661_start = rows[1]["page_start"]
    # this page has two highlights; if we add highlighting for the second one first
    # the indices for the first one will still be valid
    page_text_i661_annotated = highlight_text(
        highlight_text(
            page_text_i661,
            rows[2]["start_index"] - page_i661_start,
            rows[2]["end_index"] - page_i661_start,
        ),
        rows[1]["start_index"] - page_i661_start,
        rows[1]["end_index"] - page_i661_start,
    )


    highlight_bracketed_text(page_text_i661_annotated)
    return page_i661_start, page_text_i661_annotated


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Basic Prompt (zero-shot)""")
    return


@app.cell
def _(mo):
    # load and display the prompt

    # load prompt
    with open("prompts/quotations/basic.txt") as f0:
        basic_prompt = f0.read()
    mo.md(basic_prompt)
    return basic_prompt, f0


@app.cell
def _(
    basic_prompt,
    get_text_response,
    page_text_i256,
    page_text_i661,
    submit_prompt,
):
    # get response with the default model
    basic_responses = []
    for sample_page in [page_text_i256, page_text_i661]:
        basic_response = submit_prompt(
            task_prompt=basic_prompt, user_prompt=sample_page
        )
        basic_responses.append(basic_response)


    # get text from each response once
    basic_response_text_i256 = get_text_response(basic_responses[0])

    basic_response_text_i661 = get_text_response(basic_responses[1])
    return (
        basic_response,
        basic_response_text_i256,
        basic_response_text_i661,
        basic_responses,
        sample_page,
    )


@app.cell
def _(basic_response_text_i256, highlight_bracketed_text):
    highlight_bracketed_text(basic_response_text_i256)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""Substantial overlap with the annotated passage; it includes the full quotation, but not the preceding text included in the manual annotation.  It also excludes the author+title citation included in the manual annotation.""")
    return


@app.cell
def _(
    basic_response_text_i256,
    highlight_sidebyside,
    page_text_i256_annotated,
):
    highlight_sidebyside(page_text_i256_annotated, basic_response_text_i256)
    return


@app.cell
def _(basic_response_text_i256, html_diff, mo, page_text_i256, texts_differ):
    def show_diff_if_changed(texta, textb):
        if texts_differ(texta, textb):
            return mo.Html(html_diff(texta, textb))
        else:
            return mo.md("Text was not modified")


    show_diff_if_changed(page_text_i256, basic_response_text_i256)
    return (show_diff_if_changed,)


@app.cell
def _(
    basic_response_text_i256,
    compare_highlighted_texts,
    page_text_i256_annotated,
):
    compare_highlighted_texts(page_text_i256_annotated, basic_response_text_i256)
    return


@app.cell
def _(basic_responses, get_text_response, mo):
    response_1 = get_text_response(basic_responses[1])
    assert response_1.count("[") == response_1.count("]")
    mo.md(f"Found {response_1.count('[')} quotations")
    return (response_1,)


@app.cell
def _(basic_response_text_i661, highlight_bracketed_text):
    highlight_bracketed_text(basic_response_text_i661)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""Matches the annotated text. The highlighting doesn't make it particularly clear, but the response does include two separate quotations.""")
    return


@app.cell
def _(
    basic_response_text_i661,
    highlight_sidebyside,
    page_text_i661_annotated,
):
    highlight_sidebyside(page_text_i661_annotated, basic_response_text_i661)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        The annotated text in the response is often modified; sometimes slight variations (like whitespace or missing newlines), sometimes wildly different.

        Check for differences (other than annotation brackets) and display a difflib comparison if they have.
        """
    )
    return


@app.cell
def _(
    basic_response_text_i661,
    page_text_i661_annotated,
    show_diff_if_changed,
):
    show_diff_if_changed(page_text_i661_annotated, basic_response_text_i661)
    return


@app.cell
def _(
    basic_response_text_i661,
    compare_highlighted_texts,
    page_text_i661_annotated,
):
    compare_highlighted_texts(page_text_i661_annotated, basic_response_text_i661)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## One-shot""")
    return


@app.cell
def _(mo):
    # load prompt
    with open("prompts/quotations/one_shot.txt") as f1:
        one_shot_prompt = f1.read()
    mo.md(one_shot_prompt)
    return f1, one_shot_prompt


@app.cell
def _(
    get_text_response,
    one_shot_prompt,
    page_text_i256,
    page_text_i661,
    submit_prompt,
):
    one_shot_responses = []
    for _sample_page in [page_text_i256, page_text_i661]:
        one_shot_response = submit_prompt(
            task_prompt=one_shot_prompt, user_prompt=_sample_page
        )
        one_shot_responses.append(one_shot_response)


    # get text from each response once
    one_shot_response_text_i256 = get_text_response(one_shot_responses[0])

    one_shot_response_text_i661 = get_text_response(one_shot_responses[1])
    return (
        one_shot_response,
        one_shot_response_text_i256,
        one_shot_response_text_i661,
        one_shot_responses,
    )


@app.cell
def _(highlight_bracketed_text, one_shot_response_text_i256):
    highlight_bracketed_text(one_shot_response_text_i256)
    return


@app.cell
def _(
    highlight_sidebyside,
    one_shot_response_text_i256,
    page_text_i256_annotated,
):
    highlight_sidebyside(page_text_i256_annotated, one_shot_response_text_i256)
    return


@app.cell
def _(highlight_bracketed_text, one_shot_response_text_i661):
    highlight_bracketed_text(one_shot_response_text_i661)
    return


@app.cell
def _(
    highlight_sidebyside,
    one_shot_response_text_i661,
    page_text_i661_annotated,
):
    highlight_sidebyside(page_text_i661_annotated, one_shot_response_text_i661)
    return


@app.cell
def _(
    basic_response_text_i661,
    compare_highlighted_texts,
    one_shot_response_text_i661,
    page_text_i661_annotated,
):
    compare_highlighted_texts(
        page_text_i661_annotated,
        basic_response_text_i661,
        one_shot_response_text_i661,
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        In some runs, the results from the one-shot prompt are exactly the same as the zero-shot.  In other runs,
        it includes spurious spans for both examples (including what appears to be quoted concepts as well as title references).
        """
    )
    return


if __name__ == "__main__":
    app.run()
