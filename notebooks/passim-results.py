import marimo

__generated_with = "0.13.11"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import polars as pl
    return mo, pl


@app.cell
def _(pl):
    df = pl.read_ndjson(
        "data/passim/output/default/out.json/part-00000-dbd8cab7-6c9f-4866-b676-ff2bcd4b0890-c000.json"
    )
    df
    return (df,)


@app.cell
def _(df, mo):
    unique_clusters = len(df["cluster"].unique())
    cluster_sizes = ",".join([str(s) for s in df["size"].unique().to_list()])

    mo.md(f"Found **{unique_clusters}** clusters of size **{cluster_sizes}**.")
    return


@app.cell
def _(df, mo, pl):
    output = []

    for cluster, rows in df.group_by("cluster"):
        dnz_content = rows.filter(pl.col("series") == "dnz").row(0, named=True)
        mega_content = rows.filter(pl.col("series") == "mega").row(0, named=True)

        output.append(f"#### {dnz_content['id']} <> MEGA {mega_content['id']}")
        output.append("**DNZ text:**\n")
        output.append(dnz_content["text"])
        output.append("\n**MEGA text:**\n")
        output.append(mega_content["text"])
        output.append("---")


    mo.md("\n".join(output))
    return


if __name__ == "__main__":
    app.run()
