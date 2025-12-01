"""
The marimo notebook corresponding to the `remarx` application. The application
can be launched by running the command `remarx-app` or via marimo.

Example Usage:

    `remarx-app`

    `marimo run app.py`
"""

import marimo

__generated_with = "0.17.7"
app = marimo.App(width="medium", app_title="Quote Finder | remarx")


@app.cell
def _():
    import csv
    import marimo as mo
    import pathlib
    import tempfile

    import logging
    import remarx
    from remarx.app.utils import (
        create_header,
        create_temp_input,
        get_current_log_file,
    )

    from remarx.sentence.corpus import FileInput
    from remarx.utils import ensure_default_corpus_directories
    from remarx.quotation.pairs import find_quote_pairs
    return (
        create_header,
        find_quote_pairs,
        get_current_log_file,
        ensure_default_corpus_directories,
        logging,
        mo,
        pathlib,
    )


@app.cell
def _(create_header):
    create_header()
    return


@app.cell
def _(get_current_log_file, logging):
    # Get log file path from already configured logging
    log_file_path = get_current_log_file()

    # Log that UI started
    logger = logging.getLogger("remarx-app")
    logger.info("Remarx Quote Finder notebook started")
    return (log_file_path,)


@app.cell
def _(ensure_default_corpus_directories):
    default_dirs_ready_initial, default_dirs_initial = ensure_default_corpus_directories()
    return default_dirs_ready_initial, default_dirs_initial


@app.cell
def _(default_dirs_ready_initial, mo):
    create_dirs_btn = mo.ui.run_button(
        label="Create default corpus folders",
        disabled=default_dirs_ready_initial,
        tooltip="Create ~/remarx_corpora/original and ~/remarx_corpora/reuse",
    )
    return create_dirs_btn,


@app.cell
def _(mo):
    mo.md(r"""
    ## :mag: Quotation Finder
    Determine and identify the passages of a text corpus (**reuse**) that quote passages from texts in another corpus (**original**).
    This process requires sentence corpora (`CSVs`) created in the previous section.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### 1. Select Input CSV Files

    Browse and select CSV files for each category (currently only supports one file each):

    - **Original Sentence Corpora**: Sentence-level text corpora of the texts that we are searching for quotations of.
    - **Reuse Sentence Corpora**: Text that may contain quotations from the original text that will be detected.
    """)
    return

@app.cell
def _(
    create_dirs_btn,
    default_dirs_initial,
    default_dirs_ready_initial,
    mo,
    ensure_default_corpus_directories,
):
    default_dirs = default_dirs_initial
    default_dirs_ready = default_dirs_ready_initial

    status_msg = (
        ":white_check_mark: Default corpus folders are ready."
        if default_dirs_ready_initial
        else ":x: Default corpus folders were not found."
    )
    callout_kind = "success" if default_dirs_ready_initial else "warn"

    if create_dirs_btn.value and not default_dirs_ready_initial:
        default_dirs_ready, default_dirs = ensure_default_corpus_directories(
            create_if_missing=True
        )
        status_msg = (
            f"Created default corpus folders under `{default_dirs.root}`"
        )
        callout_kind = "success"

    mo.callout(
        mo.vstack(
            [
                mo.md("""
                By default, these two folders are used as the default location for selecting original and reuse sentence corpora if default corpus folders were created.
                """),
                mo.md(
                    f"""
                - **Original corpora**: `{default_dirs.original}`
                - **Reuse corpora**: `{default_dirs.reuse}`
                """
                ),
                mo.md(status_msg),
                create_dirs_btn,
            ]
        ),
        kind=callout_kind,
    )
    return default_dirs_ready, default_dirs



@app.cell
def _(default_dirs, default_dirs_ready, mo, pathlib):
    reuse_start = default_dirs.reuse if default_dirs_ready else pathlib.Path.home()
    original_start = (
        default_dirs.original if default_dirs_ready else pathlib.Path.home()
    )
    # Create file browsers for quotation detection (CSV files only)
    original_csv_browser = mo.ui.file_browser(
        selection_mode="file",
        multiple=True,
        initial_path=original_start,
        filetypes=[".csv"],
    )

    reuse_csv_browser = mo.ui.file_browser(
        selection_mode="file",
        multiple=True,
        initial_path=reuse_start,
        filetypes=[".csv"],
    )
    return original_csv_browser, reuse_csv_browser


@app.cell
def _(mo, original_csv_browser, reuse_csv_browser):
    # Process file selections for quotation detection
    original_csvs = original_csv_browser.value or []
    reuse_csvs = reuse_csv_browser.value or []

    original_msg = (
        f"{len(original_csvs)} files selected"
        if original_csvs
        else "No original text files selected"
    )
    reuse_msg = (
        f"{len(reuse_csvs)} files selected"
        if reuse_csvs
        else "No reuse text files selected"
    )

    original_callout_type = "success" if original_csvs else "warn"
    reuse_callout_type = "success" if reuse_csvs else "warn"

    # Create side-by-side file browser interface
    mo.hstack(
        [
            mo.callout(
                mo.vstack(
                    [
                        mo.md(
                            "**:card_file_box: Select Original Sentence Corpora (CSVs)**"
                        ).center(),
                        original_csv_browser,
                        mo.md(original_msg),
                    ]
                ),
                kind=original_callout_type,
            ),
            mo.callout(
                mo.vstack(
                    [
                        mo.md(
                            "**:recycle: Select Reuse Sentence Corpora (CSVs)**"
                        ).center(),
                        reuse_csv_browser,
                        mo.md(reuse_msg),
                    ]
                ),
                kind=reuse_callout_type,
            ),
        ],
        widths="equal",
        gap=1.2,
    )
    return original_csvs, reuse_csvs


@app.cell
def _(mo):
    mo.md(r"""
    ### 2. Select Output Location

    Select the folder where the resulting quote pairs file should be saved.
    The output CSV file will be named based on the input files.

    *To select a folder, click the file icon to the left of the folder's name.
    A checkmark will appear when a selection is made.
    Clicking anywhere else within the folder's row will cause the browser to navigate to this folder and subsequently display any folders *within* this folder.*
    """)
    return


@app.cell
def _(default_dirs, default_dirs_ready, mo, pathlib):
    initial_dir = default_dirs.root if default_dirs_ready else pathlib.Path.home()
    select_output_dir = mo.ui.file_browser(
        selection_mode="directory",
        multiple=False,
        initial_path=initial_dir,
        filetypes=[],  # only show directories
    )
    return (select_output_dir,)


@app.cell
def _(mo, select_output_dir):
    output_dir = select_output_dir.value[0] if select_output_dir.value else None
    output_dir_msg = f"`{output_dir.path}`" if output_dir else "None selected"
    out_callout_type = "success" if output_dir else "warn"

    mo.callout(
        mo.vstack(
            [
                select_output_dir,
                mo.md(f"**Save Location:** {output_dir_msg}\n"),
            ],
        ),
        kind=out_callout_type,
    )
    return (output_dir,)


@app.cell
def _(mo):
    consolidate_quotes = mo.ui.switch(label="Consolidate quotes", value=True)


    mo.vstack(
        [
            consolidate_quotes,
            mo.md(
                "Control whether quotes pairs that are sequential in both corpora should be consolidated."
            ),
        ]
    )
    return (consolidate_quotes,)


@app.cell
def _(mo):
    mo.md(r"""
    ### 3. Find Quote Pairs

    Click the "Find Quote Pairs" to run quote detection.
    The quote pairs for the input corpora will be saved as a CSV in the selected save location.
    This output file will be named based on the selected input files.
    """)
    return


@app.cell
def _(consolidate_quotes, mo, original_csvs, output_dir, reuse_csvs):
    # Determine inputs based on file & folder selections
    original_file = original_csvs[0] if original_csvs else None
    reuse_file = reuse_csvs[0] if reuse_csvs else None

    output_csv = None
    if original_file and reuse_file and output_dir:
        output_filename = (
            f"quote_pairs_{original_file.path.stem}_{reuse_file.path.stem}.csv"
        )
        output_csv = output_dir.path / output_filename

    original_file_msg = (
        f"`{original_file.path.name}`"
        if original_file
        else "*Please select an original corpus file*"
    )

    reuse_file_msg = (
        f"`{reuse_file.path.name}`"
        if reuse_file
        else "*Please select a reuse corpus file*"
    )

    dir_msg = (
        f"`{output_dir.path}`" if output_dir else "*Please select a save location*"
    )

    button = mo.ui.run_button(
        disabled=not (original_file and reuse_file and output_dir),
        label="Find Quote Pairs",
        tooltip="Click to find quote pairs",
    )

    mo.callout(
        mo.vstack(
            [
                mo.md(
                    f"""#### User Selections
                - **Original Corpus:** {original_file_msg}
                - **Reuse Corpus:** {reuse_file_msg}
                - **Save Location:** {dir_msg}
                - **Consolidate quotes:** {"yes" if consolidate_quotes.value else "no"}
            """
                ),
                button,
            ]
        ),
    )
    return button, original_file, output_csv, reuse_file


@app.cell
def _(
    button,
    consolidate_quotes,
    find_quote_pairs,
    mo,
    original_file,
    output_csv,
    reuse_file,
):
    # Find Quote Pairs
    finding_msg = 'Click "Find Quote Pairs" button to start'

    if button.value:
        spinner_msg = f"Finding quote pairs between {original_file.path.name} and {reuse_file.path.name}"
        with mo.status.spinner(title=spinner_msg) as _spinner:
            find_quote_pairs(
                original_corpus=[original_file.path],
                reuse_corpus=reuse_file.path,
                out_csv=output_csv,
                show_progress_bar=False,
                consolidate=consolidate_quotes.value,
            )
        finding_msg = f":white_check_mark: Quote pairs saved to: {output_csv}"

    mo.md(finding_msg).center()
    return


@app.cell
def _(log_file_path, mo):
    mo.md(f"""
    Logs are being written to: {log_file_path}
    """)
    return


if __name__ == "__main__":
    app.run()
