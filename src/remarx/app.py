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
    This process can be run multiple times for different text files.
    """
    )
    return


@app.cell
def _(mo):
    mo.md(
        r"""
    ### Select Input Text File
    Please select the text file whose sentences will be extracted to build a sentence corpus.
    Currently, only a single file may be selected.
    """
    )
    return


@app.cell
def _(mo):
    select_input_form = mo.ui.file(
        kind="area",
        filetypes=[".txt"],
    ).form(
        submit_button_label="Select Text",
        submit_button_tooltip="Click to confirm selection",
        clear_on_submit=True,
    )
    return (select_input_form,)


@app.cell
def _(mo, select_input_form):
    input_file = select_input_form.value[0] if select_input_form.value else None

    input_file_msg = f"`{input_file.name}`" if input_file else "None selected"

    mo.vstack(
        [
            select_input_form,
            mo.md(f"**Input File:** {input_file_msg}"),
        ]
    )
    return (input_file,)


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
    select_output_dir_form = mo.ui.file_browser(
        selection_mode="directory",
        multiple=False,
    ).form(
        submit_button_label="Select Folder",
        submit_button_tooltip="Click to confirm selection",
        clear_on_submit=True,
    )
    return (select_output_dir_form,)


@app.cell
def _(mo, select_output_dir_form):
    output_dir = (
        select_output_dir_form.value[0] if select_output_dir_form.value else None
    )
    dir_callout_mode = "success" if output_dir else "warning"
    output_dir_msg = f"`{output_dir.path}`" if output_dir else "None selected"

    mo.vstack(
        [
            select_output_dir_form,
            mo.md(f"**Save Location:** {output_dir_msg}"),
        ]
    )
    return (output_dir,)


@app.cell
def _(mo):
    mo.md(
        r"""
    ### Build Sentence Corpus
    Click the "Build Corpus" to run `remarx`.
    The sentence corpus for the input text will be saved as a CSV in the selected save location.
    This output file will have the same filename (but different file extension) as the selected input file.
    """
    )
    return


@app.cell
def _(input_file, mo, output_dir):
    # Determine inputs based on file & folder selections

    output_csv = (
        (output_dir.path / input_file.name).with_suffix(".csv")
        if input_file and output_dir
        else None
    )

    file_msg = (
        f"`{input_file.name}`" if input_file else "*Please select an input file*"
    )

    dir_msg = (
        f"`{output_dir.path}`"
        if output_dir
        else f"*Please select a save location."
    )

    button = mo.ui.run_button(
        disabled=not (input_file and output_dir),
        label="Build Corpus",
        tooltip="Click to build sentence corpus",
    )

    mo.vstack(
        [
            mo.md("####User Selections"),
            mo.md(f"**Input File:** {file_msg}"),
            mo.md(f"**Save Location**: {dir_msg}"),
            button,
        ]
    )
    return button, output_csv


@app.cell
def _(button, csv, input_file, mo, output_csv, output_dir, remarx):
    # Build Sentence Corpus
    building_msg = f'Click "Build Corpus" button to start'

    if button.value:
        spinner_msg = f"Building sentence corpus for {input_file.name}..."
        with mo.status.spinner(title=spinner_msg) as _spinner:
            file_text = input_file.contents.decode("utf-8")
            sentences = remarx.sentence.segment.segment_text(file_text)

            _spinner.update(
                f"Saving corpus {output_csv.name} to {output_dir.path}..."
            )
            with open(output_csv, mode="w", newline="") as file_handler:
                fieldnames = ["id", "offset", "text"]
                writer = csv.writer(file_handler)
                writer.writerow(fieldnames)
                for i, sentence in enumerate(sentences):
                    writer.writerow([i, *sentence])
            _spinner.update(f"Done!")
        building_msg = "✅ Done"

    mo.md(building_msg).center()
    return


if __name__ == "__main__":
    app.run()
