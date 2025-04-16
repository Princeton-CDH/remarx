# Citing Marx

This is work associated with the CDH project [Citing Marx](https://cdh.princeton.edu/projects/citing-marx/)

## AI Sandbox experiment

This branch contains code and data for preliminary experiments with
Princeton's AI Sandbox.


### Marimo notebook setup

Create a python virtual environment and install python dependencies:

```console
pip install -r requirements.txt
```

The notebook for selecting direct quote annotations requires
that you manually add a copy of `1896-97aCLEAN.txt` to `/data/text/`.

Use `marimo` to run notebook:

```console
marimo edit notebooks/quote-data.py
```

This notebook has been configured to save Jupyter notebook snapshots for
viewing on GitHub.

