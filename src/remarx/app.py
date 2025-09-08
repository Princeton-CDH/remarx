"""
The marimo notebook corresponding to the `remarx` application. The application
can be launched by running the command `remarx-app` or via marimo.

Example Usage:

    `remarx-app`

    `marimo run app.py`
"""

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
        rf"""
    ## Sentence Corpus Prep
    Create a sentence corpus (`CSV`) from a text.
    This process can be run multiple times for different files (currently one file at a time).
    """
    )
    return


@app.cell
def _(FileInput, mo):
    mo.md(
        rf"""
    **1. Select Input Text**

    Upload and select an input file (`{"`, `".join(FileInput.supported_types())}`) for sentence corpus creation.
    Currently, only a single file may be selected.
    """
    )
    return


@app.cell
def _(FileInput, mo):
    select_input = mo.ui.file(
        kind="area",
        filetypes=FileInput.supported_types(),
    )
    return (select_input,)


@app.cell
def _(mo, select_input):
    input_file = select_input.value[0] if select_input.value else None
    input_file_msg = f"`{input_file.name}`" if input_file else "None selected"
    input_callout_type = "success" if input_file else "warn"

    mo.callout(
        mo.vstack([select_input, mo.md(f"**Input File:** {input_file_msg}")]),
        kind=input_callout_type,
    )
    return (input_file,)


@app.cell
def _(mo):
    mo.md(
        r"""
    **2. Select Output Location**

    Select the folder where the resulting sentence corpus file should be saved.
    The output CSV file will be named based on the input file.

    *To select a folder, click the file icon to the left of the folder's name.
    A checkmark will appear when a selection is made.
    Clicking anywhere else within the folder's row will cause the browser to navigate to this folder and subsequently display any folders *within* this folder.*
    """
    )
    return


@app.cell
def _(mo, pathlib):
    select_output_dir = mo.ui.file_browser(
        selection_mode="directory",
        multiple=False,
        initial_path=pathlib.Path.home(),
        filetypes=[],  # only show directories
    )
    return (select_output_dir,)


@app.cell
def _(mo, select_output_dir):
    output_dir = select_output_dir.value[0] if select_output_dir.value else None
    dir_callout_mode = "success" if output_dir else "warning"
    output_dir_msg = f"`{output_dir.path}`" if output_dir else "None selected"
    out_callout_type = "success" if output_dir else "warn"


    mo.callout(
        mo.vstack(
            [
                select_output_dir,
                mo.md(f"**Save Location:** {output_dir_msg}"),
            ],
        ),
        kind=out_callout_type,
    )
    return (output_dir,)


@app.cell
def _(mo):
    mo.md(
        r"""
    **3. Build Sentence Corpus**

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

    mo.callout(
        mo.vstack(
            [
                mo.md(
                    f"""#### User Selections
                - **Input File:** {file_msg}
                - **Save Location**: {dir_msg}
            """
                ),
                button,
            ]
        ),
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
                create_corpus(
                    temp_path, output_csv, filename_override=input_file.name
                )
        building_msg = f"✅ Sentence corpus saved to: {output_csv}"

    mo.md(building_msg).center()
    return


if __name__ == "__main__":
    app.run()
