import marimo

__generated_with = "0.12.10"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import polars as pl

    from remarx.notebook_utils import highlight_bracketed_text
    return highlight_bracketed_text, mo, pl


@app.cell
def _(mo):
    mo.md(r"""# Title Mentions Model Responses Viewer""")
    return


@app.cell
def _(mo):
    mo.md(r"""## Input Data""")
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        #### Annotation data
        Here is our working subset of 27 title mention annotations.
        """
    )
    return


@app.cell
def _(pl):
    examples = pl.read_csv("data/title_mentions_subset.csv").select(
        ["UUID", "File", "Text", "Tags", "Marx Title Mentions"]
    )
    examples
    return (examples,)


@app.cell
def _(mo):
    mo.md(
        r"""
        #### Model response data
        Here is the "raw" model response data for these 27 examples for 2 different task prompts and 7 models available through the AI Sandbox.
        """
    )
    return


@app.cell
def _(pl):
    responses = pl.read_csv("data/model_responses/title_mentions.csv")

    responses
    return (responses,)


@app.cell
def _(mo):
    mo.md(
        """
        ## Content Filtering
        One of the examples was flagged by Azure OpenAI's content filtering system.
        """
    )
    return


@app.cell
def _(examples, pl, responses):
    filtered_prompts = responses.filter(
        pl.col("finish_reason") == "prompt_content_filter"
    ).unique("input_id")
    filtered_id = filtered_prompts.get_column("input_id").to_list()[0]

    examples.filter(pl.col("UUID") == filtered_id)
    return filtered_id, filtered_prompts


@app.cell
def _(mo):
    mo.md(r"""This example comes from 1897-98a and includes a title reference to Kapital. It was likely flagged for containing an antiquated term / current racial slur.""")
    return


@app.cell
def _(examples, filtered_id, highlight_bracketed_text, pl):
    # Get filtered text
    filtered_text = examples.filter(pl.col("UUID") == filtered_id).row(0)[2]
    highlight_bracketed_text(filtered_text)
    return (filtered_text,)


@app.cell
def _(filtered_id, pl, responses):
    # Filter out this example from responses
    filtered_responses = responses.filter(pl.col("input_id") != filtered_id)
    return (filtered_responses,)


@app.cell
def _(mo):
    mo.md(
        r"""
        ## View results
        First, select the prompt and model. Then, use the slider to explore the responses for this prompt and model combination.
        """
    )
    return


@app.cell
def _(filtered_responses, mo):
    # Define UI elements
    prompt_options = ["basic", "one_shot"]
    prompt_radio = mo.ui.radio(options=prompt_options, value="basic")
    models = sorted(
        filtered_responses.unique("model").get_column("model").to_list(),
        key=str.casefold,
    )
    model_radio = mo.ui.radio(options=models, value="gpt-4o-2024-05-13")
    return model_radio, models, prompt_options, prompt_radio


@app.cell
def _(mo, prompt_radio):
    mo.vstack(
        [
            mo.md("### Select a Prompt"),
            prompt_radio,
            mo.md(f"**Selected Prompt:** {prompt_radio.value}"),
        ]
    )
    return


@app.cell
def _(mo, model_radio):
    mo.vstack(
        [
            mo.md("### Select a Model"),
            model_radio,
            mo.md(f"**Selected Model:** {model_radio.value}"),
        ]
    )
    return


@app.cell
def _(mo):
    mo.md("""Below is the text of the selected prompt""")
    return


@app.cell
def _(prompt_radio):
    with open(f"prompts/title_mentions/{prompt_radio.value}.txt") as f:
        prompt_text = f.read()
    print(prompt_text)
    return f, prompt_text


@app.cell
def _(filtered_responses, mo, model_radio, pl, prompt_radio):
    # Filter to selected responses
    results = filtered_responses.filter(
        (pl.col("model") == model_radio.value)
        & (pl.col("prompt") == prompt_radio.value)
    ).select(["input_id", "input_file", "response"])

    # Setup results slider
    results_slider = mo.ui.slider(0, results.height - 1)
    return results, results_slider


@app.cell
def _(mo, results_slider):
    mo.vstack(
        [
            mo.md("### Select an example to view"),
            results_slider,
            mo.md(f"Selected Example: {results_slider.value}"),
        ]
    )
    return


@app.cell
def _(examples, highlight_bracketed_text, mo, pl, results, results_slider):
    # Display example details
    ex_id = results.row(results_slider.value)[0]
    example = examples.filter(pl.col("UUID") == ex_id)
    mo.output.append(mo.md(f"### Example {results_slider.value}"))
    mo.output.append(example)
    mo.output.append(
        highlight_bracketed_text(results.row(results_slider.value)[2])
    )
    mo.output.append(mo.md("\n\n\n\n"))
    return ex_id, example


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
