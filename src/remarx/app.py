import marimo

__generated_with = "0.14.17"
app = marimo.App(width="medium")


@app.cell
def _():
    import csv
    import marimo as mo
    import pathlib
    import tempfile

    import remarx
    from remarx.app_utils import create_temp_input
    from remarx.sentence.corpus.create import create_corpus
    from remarx.sentence.corpus import FileInput
    return FileInput, create_corpus, create_temp_input, mo, pathlib, remarx


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
    Create a sentence corpus (`CSV`) from a text.
    This process can be run multiple times for different files (currently one file at a time).
    """
    )
    return


@app.cell
def _(mo):
    mo.md(
        r"""
    ### Select Input Text File
    Upload and select an input file for sentence corpus creation.
    Currently, only a single file may be selected.
    """
    )
    return


@app.cell
def _(FileInput, mo):
    select_input_form = mo.ui.file(
        kind="area",
        filetypes=FileInput.supported_types(),
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
def _(mo, pathlib):
    select_output_dir_form = mo.ui.file_browser(
        selection_mode="directory",
        multiple=False,
        initial_path=pathlib.Path.home(),
        filetypes=[],  # only show directories
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
        else f"*Please select a save location*"
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
def _(button, create_corpus, create_temp_input, input_file, mo, output_csv):
    # Build Sentence Corpus
    building_msg = f'Click "Build Corpus" button to start'

    if button.value:
        spinner_msg = f"Building sentence corpus for {input_file.name}"
        with mo.status.spinner(title=spinner_msg) as _spinner:
            with create_temp_input(input_file) as temp_path:
                create_corpus(temp_path, output_csv)
            _spinner.update(f"Done!")
        building_msg = "✅ Done"

    mo.md(building_msg).center()
    return


if __name__ == "__main__":
    app.run()
