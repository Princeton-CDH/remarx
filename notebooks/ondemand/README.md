# Open OnDemand proof-of-concept with Marimo notebook/app

This folder contains a marimo notebook that was used to test running Marimo notebooks as apps through Open OnDemand.

The Open OnDemand app was configured using [a local fork](https://github.com/Princeton-CDH/ood-marimo-notebook) of an existing Open OnDemand Marimo notebook app. The fork has been modified to specify the cluster name as "della" and to comment out the `uv` package management. For testing purposes, it assumes a pre-existing conda environment named "marx" with the `remarx` package from this experimental branch installed.

## Setup

On della, with an account that has been enabled for Open OnDemand development, I checked out the `ood-marimo-notebook` repository at
`$HOME/ondemand/dev`.

The basic ood-marimo-notebook app is designed to run an editable notebook, similar to the Jupyter OnDemand app. I tested it that way at first with a conda environment, and then modified it slightly to run a specific notebook in app mode.

I manually created a Python 3.12 conda environment named "marx" and installed the `remarx` package from this branch:

```
conda create -n marx python=3.12
conda activate marx
pip install git+https://github.com/Princeton-CDH/citing-marx.git@experiments/trad-nlp
```

I had already downloaded Stanza model resources when I ran the lemmatized search via slurm, so I updated the OnDemand script to set the `STANZA_RESOURCES` environment variable to the appropriate path.

I created a `mo` directory in my scratch directory and put the marimo notebook in this folder (`test-app.py`) in that directory. The notebook allows the user to upload a text file, select files from a list on the server, enter one or more keyword terms, and then run a lemmatized search. The results are then downloadable as a CSV file.

I modified the OnDemand app slightly to run that notebook in app mode; the changes are in this branch: https://github.com/Princeton-CDH/ood-marimo-notebook/tree/poc-marx-app

The development applications can be run in dev mode from the test mydella dashboard at https://mydella-test.princeton.edu/pun/sys/dashboard/admin/dev/products

### Notes

The current OnDemand is a bare proof-of-concept, with hardcoded, pre-existing conda environment and resources; these setup steps would need to be refined and automated for real world use by multiple accounts. However, the proof-of-concept implementation shows that it's possible to run a Marimo notebook as an app through the Open OnDemand interface, with access to files and compute on the cluster.

## Additional context

I initially looked at [Open OnDemand documentation for running custom Python applications via Passenger](https://osc.github.io/ood-documentation/latest/tutorials/tutorials-passenger-apps.html). This doesn't work for Marimo, because Marimo requires ASGI and Passenger/nginx only currently support WSGI. Deploying an ASGI application behind nginx typically requires an additional server, which is then proxied by nginx.

Using an Open OnDemand interactive app seems like a better fit for running Marimo, due to the need for interactivity and web sockets. An alternative approach of developing a lightweight Python application (e.g., Flask or Django) to be deployed with Passenger + nginx could still be a good solution for this project. That approach may actually be simpler and more efficient with resources, since it is stateless and doesn't require specifying how much server time you need before starting the application.
