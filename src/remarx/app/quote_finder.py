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
        handle_default_corpus_creation,
        summarize_corpus_selection,
    )

    from remarx.sentence.corpus import FileInput
    from remarx.utils import get_default_corpus_path, get_default_quote_output_path
    from remarx.quotation.pairs import find_quote_pairs
    return (
        create_header,
        find_quote_pairs,
        get_current_log_file,
        get_default_corpus_path,
        get_default_quote_output_path,
        handle_default_corpus_creation,
        logging,
        mo,
        pathlib,
        summarize_corpus_selection,
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
def _(get_default_corpus_path):
    _ready, default_dirs_initial = get_default_corpus_path()
    return (default_dirs_initial,)


@app.cell
def _(default_dirs_initial, mo):
    create_dirs_btn = mo.ui.run_button(
        label="Create default corpus folders",
        disabled=default_dirs_initial.ready(),
        tooltip=(
            f"Create `{default_dirs_initial.original}` and "
            f"`{default_dirs_initial.reuse}`"
        ),
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
    handle_default_corpus_creation,
    mo,
):
    default_dirs_ready, default_dirs, corpus_status_msg, corpus_callout_kind = (
        handle_default_corpus_creation(create_dirs_btn, default_dirs_initial)
    )

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
                mo.md(corpus_status_msg),
                create_dirs_btn,
            ]
        ),
        kind=corpus_callout_kind,
    )
    return default_dirs, default_dirs_ready



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
def _(mo, original_csv_browser, pathlib, reuse_csv_browser):
    # Process file selections for quotation detection
    original_selections = original_csv_browser.value or []
    reuse_csvs = reuse_csv_browser.value or []

    # Convert file browser selections to paths for original corpora
    original_csvs = [pathlib.Path(_sel.path) for _sel in original_selections]

    original_msg = (
        f"{len(original_csvs)} file{'s' if len(original_csvs) > 1 else ''} selected"
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
def _(mo, original_csvs, pathlib, summarize_corpus_selection):
    original_summaries = []
    for csv_path in original_csvs:
        # summarize_corpus_selection expects an object with a path attribute or a path
        # Create a simple object with path attribute
        _selection_obj = type('obj', (object,), {'path': csv_path})()
        _summary = summarize_corpus_selection(_selection_obj)
        if _summary:
            original_summaries.append(_summary)

    if original_summaries:
        original_content = mo.vstack(
            [
                mo.md("#### Selected Original Corpora"),
                mo.ui.table(
                    original_summaries,
                    page_size=min(10, len(original_summaries)),
                    selection=None,  # display only
                    show_download=False,  # hide download control
                ).style(max_height="260px", overflow="auto"),
            ]
        )
    else:
        original_content = mo.callout("No original corpora selected yet.", kind="info")

    original_content
    return (original_summaries,)


@app.cell
def _(mo, pathlib, reuse_csvs, summarize_corpus_selection):
    reuse_summaries = []
    for _selection in reuse_csvs:
        # reuse_csvs contains file browser selection objects with a path attribute
        _sel_path = pathlib.Path(_selection.path)
        if _sel_path.is_file() and _sel_path.suffix == ".csv":
            _summary = summarize_corpus_selection(_selection)
            if _summary:
                reuse_summaries.append(_summary)

    if reuse_summaries:
        reuse_content = mo.vstack(
            [
                mo.md("#### Selected Reuse Corpora"),
                mo.ui.table(
                    reuse_summaries,
                    page_size=min(10, len(reuse_summaries)),
                    selection=None,  # display only
                    show_download=False,  # hide download control
                ).style(max_height="260px", overflow="auto"),
            ]
        )
    else:
        reuse_content = mo.callout("No reuse corpora selected yet.", kind="info")

    reuse_content
    return (reuse_summaries,)


@app.cell
def _(mo):
    mo.md(r"""
    ### 2. Select Output Location

    Select the folder where the resulting quote pairs file should be saved.
    The output CSV file will be named based on the input files.
    """)
    return


@app.cell
def _(get_default_quote_output_path):
    _ready, default_quote_output_initial = get_default_quote_output_path()
    return (default_quote_output_initial,)


@app.cell
def _(default_quote_output_initial, mo):
    create_quote_output_btn = mo.ui.run_button(
        label="Create default quote output folder",
        disabled=default_quote_output_initial.exists(),
        tooltip=f"Create `{default_quote_output_initial}`",
    )
    return create_quote_output_btn,


@app.cell
def _(mo):
    custom_output_toggle = mo.ui.switch(
        label="Use a custom output location", value=False
    )
    return custom_output_toggle,


@app.cell
def _(create_quote_output_btn, custom_output_toggle, default_quote_output_initial, get_default_quote_output_path, mo):
    # Always initialize variables
    default_quote_output_ready_initial = default_quote_output_initial.exists()
    default_quote_output = default_quote_output_initial
    default_quote_output_ready = default_quote_output_ready_initial

    # Initialize status message and callout kind unconditionally
    quote_output_status_msg = (
        ":white_check_mark: Default quote output folder is ready."
        if default_quote_output_ready_initial
        else ":x: Default quote output folder was not found."
    )
    quote_output_callout_kind = "success" if default_quote_output_ready_initial else "warn"

    # Update if button was clicked and folder didn't exist
    if create_quote_output_btn.value and not default_quote_output_ready_initial:
        default_quote_output_ready, default_quote_output = get_default_quote_output_path(
            create=True
        )
        quote_output_status_msg = f"Created default quote output folder at `{default_quote_output}`"
        quote_output_callout_kind = "success"

    mo.callout(
        mo.vstack(
            [
                mo.md("""
                By default, quote pair outputs are saved to the default quote output folder if it exists.
                """),
                mo.md(f"**Default location:** `{default_quote_output}`"),
                mo.md(quote_output_status_msg),
                create_quote_output_btn,
                mo.md("---"),
                mo.md("""
                    **Option 1:** Output to default folder (recommended)
                """),
                mo.md("---"),
                mo.md("""
                    **Option 2:** Toggle custom output if you prefer to browse to a different folder
                """),
                custom_output_toggle,
            ]
        ),
        kind=quote_output_callout_kind,
    )
    return default_quote_output, default_quote_output_ready


@app.cell
def _(default_quote_output, default_quote_output_ready, mo, pathlib):
    initial_dir = (
        default_quote_output if default_quote_output_ready else pathlib.Path.home()
    )
    select_output_dir = mo.ui.file_browser(
        selection_mode="directory",
        multiple=False,
        initial_path=initial_dir,
        filetypes=[],  # only show directories
    )
    return (select_output_dir,)


@app.cell
def _(
    custom_output_toggle,
    default_quote_output,
    default_quote_output_ready,
    mo,
    pathlib,
    select_output_dir,
):
    output_dir_path: pathlib.Path | None = None
    save_callout_kind = "success"
    callout_contents: list = []

    if custom_output_toggle.value:
        selected_dir = select_output_dir.value[0] if select_output_dir.value else None
        output_dir_path = (
            pathlib.Path(selected_dir.path) if selected_dir is not None else None
        )
        save_callout_kind = "success" if output_dir_path else "warn"
        output_msg = (
            f"**Save Location:** `{output_dir_path}`"
            if output_dir_path
            else "No custom folder selected"
        )
        callout_contents = [
            mo.md("Select a custom folder to save the quote pairs."),
            mo.md("""
                *To select a folder, click the file icon to the left of the folder's name.
A checkmark will appear when a selection is made.
Clicking anywhere else within the folder's row will cause the browser to navigate to this folder and subsequently display any folders *within* this folder.*
            """
            ),
            select_output_dir,
            mo.md(output_msg),
        ]
    else:
        if default_quote_output_ready:
            output_dir_path = default_quote_output
            callout_contents = [
                mo.md(
                    "The quote pairs will be saved under the default folder shown above."
                ),
                mo.md(f"**Save Location:** `{default_quote_output}`"),
            ]
            save_callout_kind = "success"
        else:
            callout_contents = [
                mo.md(
                    "Default folder is not available. Create it above or toggle custom output to choose a location."
                )
            ]
            save_callout_kind = "warn"

    mo.callout(
        mo.vstack(callout_contents),
        kind=save_callout_kind,
    )
    return (output_dir_path,)


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
def _(consolidate_quotes, mo, original_csvs, output_dir_path, pathlib, reuse_csvs):
    # Determine inputs based on file & folder selections
    # original_csvs is now a list of pathlib.Path objects
    # reuse_csvs is still a list of file browser selection objects
    reuse_file = reuse_csvs[0] if reuse_csvs else None
    reuse_file_path = pathlib.Path(reuse_file.path) if reuse_file else None

    output_csv = None
    if original_csvs and reuse_file_path and output_dir_path:
        # Create output filename based on reuse file and number of original files
        if len(original_csvs) == 1:
            output_filename = (
                f"quote_pairs_{original_csvs[0].stem}_{reuse_file_path.stem}.csv"
            )
        else:
            output_filename = (
                f"quote_pairs_{len(original_csvs)}_originals_{reuse_file_path.stem}.csv"
            )
        output_csv = output_dir_path / output_filename

    original_file_msg = (
        f"{len(original_csvs)} file{'s' if len(original_csvs) > 1 else ''}"
        if original_csvs
        else "*Please select original corpus file(s)*"
    )

    reuse_file_msg = (
        f"`{reuse_file_path.name}`"
        if reuse_file_path
        else "*Please select a reuse corpus file*"
    )

    dir_msg = (
        f"`{output_dir_path}`" if output_dir_path else "*Please select a save location*"
    )

    button = mo.ui.run_button(
        disabled=not (original_csvs and reuse_file_path and output_dir_path),
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
    return button, output_csv, reuse_file_path


@app.cell
def _(
    button,
    consolidate_quotes,
    find_quote_pairs,
    mo,
    original_csvs,
    output_csv,
    reuse_file_path,
):
    # Find Quote Pairs
    finding_msg = 'Click "Find Quote Pairs" button to start'

    if button.value:
        _original_count = len(original_csvs)
        if _original_count == 1:
            spinner_msg = f"Finding quote pairs between {original_csvs[0].name} and {reuse_file_path.name}"
        else:
            spinner_msg = f"Finding quote pairs between {_original_count} original files and {reuse_file_path.name}"
        with mo.status.spinner(title=spinner_msg) as _spinner:
            find_quote_pairs(
                original_corpus=original_csvs,
                reuse_corpus=reuse_file_path,
                output_path=output_csv,
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
