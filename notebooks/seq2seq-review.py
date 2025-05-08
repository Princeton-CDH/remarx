

import marimo

__generated_with = "0.13.3"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""# Review seq2seq results in context""")
    return


@app.cell
def _():
    import polars as pl
    return (pl,)


@app.cell
def _(pl):
    quotes_df = pl.read_csv("data/seq2seq/quotes.csv")
    quotes_df
    return (quotes_df,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ## Adjust offsets to match annotated text files

        `seq2seq` can't handle longer files (memory limitations). For convenience, I fed it the articles that were split out from the first set of "cleaned" texts. If we can find the offset of these files in the cleaned text they come from, then we can adjust offsets and look at the quotation data in context — hopefully there are a few adjacent to annotated data.

        Get a list of unique files referenced in the quotation data:
        """
    )
    return


@app.cell
def _(mo, pl, quotes_df):
    # the filename without the .txt extension was added to the cleaned text file
    #
    quote_source_files = (
        quotes_df["file"]
        .map_elements(lambda x: x.rsplit(".", 1)[0], return_dtype=pl.String)
        .unique()
        .to_list()
    )
    mo.ui.table(quote_source_files, selection=None)
    return (quote_source_files,)


@app.cell
def _(mo, pl, quote_source_files):
    import pathlib

    input_offset_file = pathlib.Path("data/seq2seq/input_offsets.csv")

    if not input_offset_file.exists():
        print(
            f"Input offset file {input_offset_file} not found, determining offsets."
        )
        clean_full_text_dir = pathlib.Path(
            "data/neue-zeit-full_transcriptions/Edited/"
        )
        if not clean_full_text_dir.is_dir():
            print("Directory with clean full-text files not found.")

        # list of filenames to find
        to_find = set(quote_source_files)
        # list of dictionaries for found filenames with text file name and character offset
        file_offsets = []

        for textfile in clean_full_text_dir.glob("*.txt"):
            contents = textfile.open().read()
            for filename in list(to_find):
                file_index = contents.find(filename)
                if file_index != -1:
                    file_offsets.append(
                        {
                            "file": f"{filename}.txt",  # file is the field name in the quote data
                            "text_file": textfile.name,
                            "offset": file_index,
                        }
                    )
                    # remove the filename from the list once it is found
                    to_find.remove(filename)

        if not len(to_find) == 0:
            print("Did not find index for: {to_find}")
        else:
            print("Found starting offset for all seq2seq input files.")

        input_offset_file = pathlib.Path("data/seq2seq/input_offsets.csv")
        input_offset_df = pl.from_dicts(file_offsets)
        input_offset_df.write_csv(input_offset_file)
    else:
        print(
            f"Loading previously calculated input file source offsets from {input_offset_file}."
        )
        input_offset_df = pl.read_csv(input_offset_file)

    mo.ui.table(input_offset_df, selection=None)
    return (input_offset_df,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        All of these files are from a cleaned text file that have not yet been annotated. 😕

        We can't compare with human annotation, but maybe viewing in context will still be helpful.
        """
    )
    return


@app.cell
def _(input_offset_df, quotes_df):
    # join seq2seq quotes data with input file offsets so we can calculate offset in the annotated file

    quotes_source_text = quotes_df.join(input_offset_df, on="file")
    quotes_source_text
    return


if __name__ == "__main__":
    app.run()
