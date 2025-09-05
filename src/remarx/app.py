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
def _(FileInput, mo):
    # Define the sentence corpus creation section content
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

    input_selection_ui = mo.callout(
        mo.vstack([select_input, mo.md(f"**Input File:** {input_file_msg}")]),
        kind=input_callout_type,
    )
    return (input_file, input_selection_ui)


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

    output_selection_ui = mo.callout(
        mo.vstack(
            [
                select_output_dir,
                mo.md(f"**Save Location:** {output_dir_msg}"),
            ],
        ),
        kind=out_callout_type,
    )
    return (output_dir, output_selection_ui)


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

    build_corpus_ui = mo.callout(
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
    return button, output_csv, build_corpus_ui


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

    corpus_status_ui = mo.md(building_msg).center()
    return (corpus_status_ui,)


@app.cell
def _(FileInput, build_corpus_ui, corpus_status_ui, input_selection_ui, mo, output_selection_ui):
    # Create the sentence corpus creation content
    sentence_corpus_creation_content = mo.vstack([
        mo.md(
            f"""
        Create a sentence corpus (`CSV`) from a text.
        This process can be run multiple times for different files (currently one file at a time).

        **1. Select Input Text**

        Upload and select an input file (`{"`, `".join(FileInput.supported_types())}`) for sentence corpus creation.
        Currently, only a single file may be selected.
        """
        ).style(width="100%"),

        input_selection_ui,

        mo.md(
            """
        **2. Select Output Location**

        Select the folder where the resulting sentence corpus file should be saved.
        The output CSV file will be named based on the input file.

        *To select a folder, click the file icon to the left of the folder's name.
        A checkmark will appear when a selection is made.
        Clicking anywhere else within the folder's row will cause the browser to navigate to this folder and subsequently display any folders *within* this folder.*
        """
        ).style(width="100%"),

        output_selection_ui,

        mo.md(
            """
        **3. Build Sentence Corpus**

        Click the "Build Corpus" to run `remarx`.
        The sentence corpus for the input text will be saved as a CSV in the selected save location.
        This output file will have the same filename (but different file extension) as the selected input file.
        """
        ).style(width="100%"),

        build_corpus_ui,
        corpus_status_ui,
    ])

    return (sentence_corpus_creation_content,)


@app.cell
def _(mo, pathlib):
    # Create file browsers for quotation detection (CSV files only)
    original_csv_browser = mo.ui.file_browser(
        selection_mode="file",
        multiple=True,
        initial_path=pathlib.Path.home(),
        filetypes=[".csv"],
    )

    reuse_csv_browser = mo.ui.file_browser(
        selection_mode="file",
        multiple=True,
        initial_path=pathlib.Path.home(),
        filetypes=[".csv"],
    )

    return (original_csv_browser, reuse_csv_browser)


@app.cell
def _(mo, original_csv_browser, reuse_csv_browser):
    # Process file selections for quotation detection
    original_csvs = original_csv_browser.value if original_csv_browser.value else []
    reuse_csvs = reuse_csv_browser.value if reuse_csv_browser.value else []

    original_count = len(original_csvs)
    reuse_count = len(reuse_csvs)

    original_msg = f"{original_count} file(s) selected" if original_count > 0 else "No files selected"
    reuse_msg = f"{reuse_count} file(s) selected" if reuse_count > 0 else "No files selected"

    original_callout_type = "success" if original_count > 0 else "warn"
    reuse_callout_type = "success" if reuse_count > 0 else "info" # use a different color

    # Create side-by-side file browser interface
    quotation_file_selection_ui = mo.hstack([
        mo.callout(
            mo.vstack([
                mo.md("# 🗂").center(),
                mo.md("**Original Text CSV Files**").center(),
                mo.md("*Select sentence corpus files for original texts*").center(),
                original_csv_browser,
                mo.md(f"**Selected:** {original_msg}")
            ]),
            kind=original_callout_type,
        ),
        mo.callout(
            mo.vstack([
                mo.md("# ♻️").center(),
                mo.md("**Reuse Text CSV Files**").center(),
                mo.md("*Select sentence corpus files for reuse texts*").center(),
                reuse_csv_browser,
                mo.md(f"**Selected:** {reuse_msg}")
            ]),
            kind=reuse_callout_type,
        )
    ], widths="equal", gap=1.2)

    return (original_csvs, reuse_csvs, quotation_file_selection_ui)


@app.cell
def _(mo, original_csvs, reuse_csvs, quotation_file_selection_ui):
    # Create quotation detection content
    quotation_detection_content = mo.vstack([
        mo.md(
            """
            Detect quotations and text reuse between original and reuse texts.
            This process requires sentence corpus CSV files created in the previous step.

            **1. Select Input CSV Files**

            Browse and select one or multiple CSV files for each category:
            """
        ).style(width="100%"),

        quotation_file_selection_ui,

        mo.md(
            """
            **More features coming soon!**

            - Configure detection parameters
            - Run quotation analysis
            - Export results

            Stay tuned for this functionality.
            """
        ).style(width="100%"),
    ])

    return (quotation_detection_content,)


@app.cell
def _(mo, sentence_corpus_creation_content, quotation_detection_content):
    # Create the main accordion with different sections
    mo.accordion({
        "## 📝 Sentence Corpus Creation": sentence_corpus_creation_content,
        "## 🔍 Quotation Detection": quotation_detection_content,
    })
    return


if __name__ == "__main__":
    app.run()
