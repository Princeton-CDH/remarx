import marimo

__generated_with = "0.14.16"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    import remarx

    return mo, remarx


@app.cell
def _(mo):
    mo.vstack(
        [
            mo.md("# `remarx`").center(),
            mo.md(
                "This is the preliminary graphical user interface for the `remarx` software tool."
            ).center(),
        ]
    )
    return


@app.cell
def _(mo):
    mo.md(
        r"""
    ## Check `remarx` version number
    Click the button below to display the running version number of `remarx`.
    """
    )
    return


@app.cell
def _(mo):
    version_button = mo.ui.run_button(label="Show Version")
    return (version_button,)


@app.cell
def _(version_button):
    version_button
    return


@app.cell
def _(mo, remarx, version_button):
    display_text = None
    callout_type = None
    if version_button.value:
        display_text = f"**remarx version:** {remarx.__version__}"
        callout_type = "neutral"
    else:
        display_text = "*Click the button above!*"
        callout_type = "info"

    mo.md(display_text).callout(callout_type)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
