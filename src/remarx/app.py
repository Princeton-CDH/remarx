import marimo

__generated_with = "0.14.16"
app = marimo.App(width="medium")


@app.cell
def _():
    import csv
    import marimo as mo

    import remarx
    from remarx.sentence.segment import segment_text
    return csv, mo, remarx


@app.cell
def _(mo, sys):
    # Launch notebook if its being run as as script
    from marimo._cli import cli

    if not mo.running_in_notebook():
        try:
            cli.main(["run", __file__])
        except KeyboardInterrupt:
            sys.exit(0)
    return


@app.cell
def _(mo):
    mo.vstack(
        [
            mo.md("# `remarx`: Quotation Finder").center(),
            mo.md(
                "This is the preliminary graphical user interface for the `remarx` software tool."
            ).center(),
        ]
    )
    return


@app.cell
def _(mo, remarx):
    mo.md(rf"""Running `remarx` version: {remarx.__version__}""")
    return


@app.cell
def _(mo):
    mo.md(
        r"""
    ## Sentence Corpus Prep
    Create a sentence corpus (`CSV`) from a text file.
    """
    )
    return


@app.cell
def _(mo):
    mo.md(
        r"""
    ### Select Input Text File
    Please select the text file whose sentences will be extracted to build a sentence corpus.
    """
    )
    return


@app.cell
def _(mo):
    select_input_file = mo.ui.file(kind="area", filetypes=[".txt"])
    select_input_file
    return (select_input_file,)


@app.cell
def _(mo):
    mo.md(
        r"""
    ## Select Output Location
    Select the folder where the resulting sentence corpus file should be saved.
    The output CSV file will be named based on the input file.
    """
    )
    return


@app.cell
def _(mo):
    select_output_dir = mo.ui.file_browser(
        selection_mode="directory",
        multiple=False,
    )
    select_output_dir
    return (select_output_dir,)


@app.cell
def _(select_input_file, select_output_dir):
    is_ready = any(select_input_file.value) and any(select_output_dir.value)
    is_ready
    return (is_ready,)


@app.cell
def _(mo):
    mo.md(
        r"""
    ### Build Sentence Corpus
    Click the "Build Corpus" to run `remarx`.
    The sentence corpus for the input text will be saved as a CSV in the selected save location.
    This output file will have the same filename (but different file extension) as the selected input file.

    The button will be disabled (grayed out) until both the input text file and save location have been selected.
    """
    )
    return


@app.cell
def _(is_ready, mo):
    button = mo.ui.run_button(disabled=not is_ready, label="Build Corpus")
    button
    return (button,)


@app.cell
def _(button, csv, remarx, select_input_file, select_output_dir):
    # Build Sentence Corpus
    if button.value:
        # Get input values
        input_file = select_input_file.value[0]
        output_dir = select_output_dir.value[0]
        # Determine output csv path
        output_csv = (output_dir.path / input_file.name).with_suffix(".csv")

        print(f"Building Sentence Corpus for {input_file.name}...")
        file_text = input_file.contents.decode("utf-8")
        sentences = remarx.sentence.segment.segment_text(file_text)

        print(f"Saving corpus {output_csv.name} to {output_dir.path}")
        with open(output_csv, mode="w", newline="") as file_handler:
            fieldnames = ["id", "offset", "text"]
            writer = csv.writer(file_handler)
            writer.writerow(fieldnames)
            for sentence in sentences:
                writer.writerow(sentence)
        print("Done!")
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
