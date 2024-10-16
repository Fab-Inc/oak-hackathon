# fab-oak-hackathon

<a target="_blank" href="https://cookiecutter-data-science.drivendata.org/">
    <img src="https://img.shields.io/badge/CCDS-Project%20template-328F97?logo=cookiecutter" />
</a>

Oak National API Hackathon

## Project Organization

```
├── .env               <- Environment variables (don't check this in to git)
├── LICENSE            <- Open-source license if one is chosen
├── README.md          <- The top-level README for developers using this project.
├── data
│   ├── external       <- Data from third party sources.
│   ├── interim        <- Intermediate data that has been transformed.
│   ├── processed      <- The final, canonical data sets for modeling.
│   └── raw            <- The original, immutable data dump.
│
├── scripts            <- Interactive scripts and Jupyter notebooks. Naming convention is a number (for ordering),
│                         the creator's initials, and a short `-` delimited description, e.g.
│                         `1.0-jqp-initial-data-exploration`.
│
├── pyproject.toml     <- Project configuration file with package metadata 
│                         and configuration for tools like black
│
├── references         <- Data dictionaries, manuals, and all other explanatory materials.
│
├── reports            <- Generated analysis as HTML, PDF, LaTeX, etc.
│   └── figures        <- Generated graphics and figures to be used in reporting
│
├── pixi.lock          <- The pixi lock file for reproducing the environment
│
├── setup.cfg          <- Configuration file for flake8
│
└── oakhack   <- Source code for use in this project.
    │
    ├── __init__.py             <- Makes hackathon a Python module
    │
    ├── config.py               <- Store useful variables and configuration
    │
    └── plots.py                <- Code to create visualizations
```

--------

# Fab Inc Oak National API Hackathon

This repo loosely follows the [Cookie Cutter Data Science](https://cookiecutter-data-science.drivendata.org/) (CCDS) template, but makes use of [pixi](https://pixi.sh) for environment management and [DVC](https://dvc.org/) for data version control. More details of the opinions behinds CCDS are available [here](https://cookiecutter-data-science.drivendata.org/opinions/).

Put scripts, notebooks and interactive work in [scripts/](scripts), with your initials in a descriptive filename (not sure about the numbering system). Any code that is to be reused across files should go in the [`oakhack`](oakhack) module. 

## Pixi environment

Make sure you install the latest version of [pixi](https://pixi.sh) (at least 0.32.1). On Mac you can install this with [Homebrew](https://brew.sh/).

Running `pixi shell` inside the project folder should recreate the environment precisely, including the `dvc` executbale. 

For VSCode you might need to install the [pixi extension](https://marketplace.visualstudio.com/items?itemName=jjjermiah.pixi-vscode) to be able to chose the project's Python environment (in `.pixi/` in the project folder).

## DVC for data


