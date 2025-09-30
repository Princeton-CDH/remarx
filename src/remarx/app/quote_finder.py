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

    import remarx
    from remarx.app.utils import create_header, create_temp_input
    from remarx.sentence.corpus import FileInput
    return FileInput, create_header, mo, pathlib


@app.cell
def _(create_header):
    create_header()
    return

@app.cell
def _(configure_logging, logging):
    # Set up logging and get log file path
    log_file_path = configure_logging()

    # Log that UI started
    logger = logging.getLogger("remarx-app")
    logger.info("Remarx Quote Finder notebook started")

    return (log_file_path,)

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
def _(mo):
    mo.md(
        r"""
    ## 🔍 Quotation Finder
    Determine and identify the passages of a text corpus (**reuse**) that quote passages from texts in another corpus (**original**).
    This process requires sentence corpora (`CSVs`) created in the previous section.
    """
    )
    return


@app.cell
def _(mo):
    mo.md(
        r"""
    ### 1. Select Input CSV Files

    Browse and select one or more CSV files for each category:

    - **Original Sentence Corpora**: Sentence-level text corpora of the texts that we are searching for quotations of.
    - **Reuse Sentence Corpora**: Text that may contain quotations from the original text that will be detected.
    """
    )
    return


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
                            "**🗂 Select Original Sentence Corpora (CSVs)**"
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
                            "**♻️ Select Reuse Sentence Corpora (CSVs)**"
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
    return


if __name__ == "__main__":
    app.run()
