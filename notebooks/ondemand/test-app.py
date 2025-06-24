import marimo

__generated_with = "0.13.11"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from pathlib import Path
    return Path, mo


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""# marimo test OnDemand app""")
    return


@app.cell
def _(mo):
    mo.md(f"""This notebook is running at: \n\n`{mo.notebook_location()}`""")
    return


@app.cell(hide_code=True)
def _(Path, mo):
    user_data_dir = Path(".") / "uploads"
    user_data_dir.mkdir(exist_ok=True)
    result_dir = Path(".") / "results"
    result_dir.mkdir(exist_ok=True)


    def save_uploaded_files(upload_results):
        "when files are uploaded, save them to the user data dir"
        print(upload_results)
        for upload_value in upload_results:
            upload_file = user_data_dir / upload_value.name
            upload_file.write_bytes(upload_value.contents)


    upload_files = mo.ui.file(
        kind="area",
        filetypes=[".txt"],
        multiple=True,
        on_change=save_uploaded_files,
    )
    upload_files
    return result_dir, user_data_dir


@app.cell(hide_code=True)
def _(mo, user_data_dir):
    file_browser = mo.ui.file_browser(initial_path=user_data_dir, multiple=True)
    file_browser
    return (file_browser,)


@app.cell
def _(mo):
    search_phrases = mo.ui.text_area()
    mo.vstack([mo.md("Enter search phrases, one per line:"), search_phrases])
    return (search_phrases,)


@app.cell(hide_code=True)
def _(mo, result_dir):
    output_path = None


    def set_output_path(output_filename):
        if not output_filename.endswith(".csv"):
            output_filename = f"{output_filename}.csv"
        global output_path
        output_path = result_dir / output_filename


    output_filename_input = mo.ui.text(
        label="Output filename:", on_change=set_output_path
    )
    output_filename_input
    return output_filename_input, output_path


@app.cell
def _(file_browser, mo, output_filename_input, output_path, search_phrases):
    from remarx.candidate_mentions import save_candidate_sentences


    download_ready = False


    def check_download_ready():
        global download_ready
        download_ready = output_path is not None and output_path.exists()


    def search_and_save(_value):
        err = False
        if not file_browser.value:
            mo.output.append(mo.md("Please select at least one input file."))
            err = True
        if not search_phrases.value.strip():
            mo.output.append(mo.md("Please input at least one search term."))
            err = True
        if not output_filename_input.value.strip():
            mo.output.append(mo.md("Please input a filename for the results."))
            err = True
        # check if output file already exists (candidate sentence method will balk)
        elif output_path.exists():
            mo.output.append(
                mo.md(
                    f"Output filename `{output_path.name}` already exists; choose a different name."
                )
            )
            err = True
        if err:
            # redisplay submit button (otherwise seems to disappear)
            mo.output.append(submit_button)
            return

        input_files = [selected_file.path for selected_file in file_browser.value]
        search_terms = [p.strip() for p in search_phrases.value.split()]

        with mo.status.spinner(subtitle="Searching files ...") as _spinner:
            save_candidate_sentences(
                input_files,
                search_terms,
                output_path,
            )

        # if output file was created, display download button
        if output_path.exists():
            # Eager loading download file (lazy loading also possible)
            download_result = mo.download(
                data=output_path.read_text(),
                filename=output_path.name,
                mimetype="text/csv",
            )
            mo.output.append(download_result)


    submit_button = mo.ui.button(
        on_click=search_and_save, label="Search", kind="neutral"
    )

    submit_button
    return


@app.cell
def _(mo):
    # when running through ondemand, there's no way to exit;
    # this will at least shutdown the notebook  (maybe not super graceful)
    # solution from https://github.com/marimo-team/marimo/discussions/3614

    import signal

    def exit_app(_value):
        signal.raise_signal(signal.SIGTERM)


    exit_button = mo.ui.button(label="Shutdown", kind="warn", on_click=exit_app)
    exit_button
    return


if __name__ == "__main__":
    app.run()
