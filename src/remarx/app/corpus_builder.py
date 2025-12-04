"""
The marimo notebook corresponding to the `remarx` application. The application
can be launched by running the command `remarx-app` or via marimo.

Example Usage:

    `remarx-app`

    `marimo run app.py`
"""

import marimo

__generated_with = "0.15.2"
app = marimo.App(width="medium")


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
    )
    from remarx.app.log_viewer import render_log_panel
    from remarx.sentence.corpus.create import create_corpus
    from remarx.sentence.corpus import FileInput
    from remarx.utils import get_default_corpus_path
    return (
        FileInput,
        create_corpus,
        create_header,
        create_temp_input,
        get_current_log_file,
        handle_default_corpus_creation,
        get_default_corpus_path,
        mo,
        pathlib,
        remarx,
        logging,
        render_log_panel,
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
    logger.info("Remarx Corpus Builder notebook started")

    return (log_file_path,)


@app.cell
def _(mo):
    mo.md(
        rf"""
    ## 📝 Sentence Corpus Builder
    Create a sentence corpus (`CSV`) from a text.
    This process can be run multiple times for different files (currently one file at a time).
    """
    )
    return


@app.cell
def _(FileInput, mo):
    mo.md(
        rf"""
    ### 1. Select Input Text

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
    ### 2. Select Output Location

    Select the folder where the resulting sentence corpus file should be saved.
    The output CSV file will be named based on the input file.
    """
    )
    return


@app.cell
def _(get_default_corpus_path):
    _ready, default_dirs_initial = get_default_corpus_path()
    return (default_dirs_initial,)


@app.cell
def _(default_dirs_initial, mo):
    default_dirs_ready_initial = default_dirs_initial.ready()
    create_default_dirs_btn = mo.ui.run_button(
        label="Create default corpus folders",
        disabled=default_dirs_ready_initial,
        tooltip=(
            f"Create `{default_dirs_initial.original}` and "
            f"`{default_dirs_initial.reuse}`"
        ),
    )
    return create_default_dirs_btn,


@app.cell
def _(mo):
    default_folder_choice = mo.ui.radio(
        options={
            "the default original corpus folder": "original",
            "the default reuse corpus folder": "reuse",
        },
        value="the default original corpus folder",
        label="Choose which folder to save the current sentence corpus in:",
    )
    return default_folder_choice,


@app.cell
def _(mo):
    custom_output_toggle = mo.ui.switch(
        label="Use a custom output location", value=False
    )
    return custom_output_toggle,


@app.cell
def _(
    create_default_dirs_btn,
    custom_output_toggle,
    default_dirs_initial,
    default_folder_choice,
    handle_default_corpus_creation,
    mo,
):
    folder_choice_display = (
        default_folder_choice
        if not custom_output_toggle.value
        else default_folder_choice.style(pointer_events="none", opacity=0.6)
    )

    default_dirs_ready, default_dirs, status_msg, _callout_kind = (
        handle_default_corpus_creation(
            create_default_dirs_btn,
            default_dirs_initial,
        )
    )

    mo.callout(
        mo.vstack(
            [
                mo.md(
                    """
                We recommend saving corpora inside dedicated folders under your home directory. By default, corpora are saved to these two places:
                """
                ),
                mo.md(
                    f"""
                - **Original corpora**: `{default_dirs.original}`
                - **Reuse corpora**: `{default_dirs.reuse}`
                """
                ),
                mo.md(status_msg),
                create_default_dirs_btn,
                mo.md("---"),
                mo.md("""
                    **Option 1:** Output to default folders
                """),
                folder_choice_display,
                mo.md("---"),
                mo.md("""
                    **Option 2:** Toggle custom output if you prefer to browse to a different folder
                """
                ),
                custom_output_toggle,
            ]
        ),
        kind=_callout_kind,
    )
    return default_dirs_ready, default_dirs


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
def _(
    custom_output_toggle,
    default_dirs,
    default_dirs_ready,
    default_folder_choice,
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
            mo.md("Select a custom folder to save the sentence corpus."),
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
        if default_dirs_ready:
            target = (
                default_dirs.original
                if default_folder_choice.value == "original"
                else default_dirs.reuse
            )
            output_dir_path = target
            callout_contents = [
                mo.md(
                    "The corpus will be saved under the default folders shown above."
                ),
                mo.md(f"**Save Location:** `{target}`"),
            ]
            save_callout_kind = "success"
        else:
            callout_contents = [
                mo.md(
                    "Default folders are not available. Create them above or toggle custom output to choose a location."
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
    mo.md(
        r"""
    ### 3. Build Sentence Corpus

    Click the "Build Corpus" to run `remarx`.
    The sentence corpus for the input text will be saved as a CSV in the selected save location.
    This output file will have the same filename (but different file extension) as the selected input file.
    """
    )
    return


@app.cell
def _(mo):
    log_refresh = mo.ui.refresh(options=["1s"], default_interval="1s")
    return (log_refresh,)


@app.cell
def _(input_file, mo, output_dir_path):
    # Determine inputs based on file & folder selections

    output_csv = (
        (output_dir_path / input_file.name).with_suffix(".csv")
        if input_file and output_dir_path
        else None
    )

    file_msg = (
        f"`{input_file.name}`" if input_file else "*Please select an input file*"
    )

    dir_msg = (
        f"`{output_dir_path}`"
        if output_dir_path
        else f"*Please select a save location*"
    )

    button = mo.ui.run_button(
        disabled=not (input_file and output_dir_path),
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
    building_msg = 'Click "Build Corpus" button to start, and then **refresh the page** to see the real-time process logging below'

    if button.value:
        spinner_msg = f"Building sentence corpus for {input_file.name}"
        with mo.status.spinner(title=spinner_msg) as _spinner:
            with create_temp_input(input_file) as temp_path:
                create_corpus(
                    temp_path, output_csv, filename_override=input_file.name
                )
        building_msg = f":white_check_mark: Sentence corpus saved to: {output_csv}"

    mo.md(building_msg).center()
    return


@app.cell
def _(log_file_path, log_refresh, mo, render_log_panel):
    mo.vstack(
        [
            mo.md("### Live remarx logs"),
            render_log_panel(
                log_file_path,
                refresh_control=log_refresh,
                refresh_ticks=log_refresh.value,
            ),
        ],
        align="stretch",
        gap="0.75em",
    )
    return


@app.cell
def _(mo, log_file_path):
    mo.md(f"Logs are being written to: {log_file_path}")
    return


if __name__ == "__main__":
    app.run()
