

Export your Github personal data: issues, PRs, comments, followers and
followings, etc.

**Note**: this only deals with metadata. If you want a download of
actual git repositories, I recommend using
[python-github-backup](https://github.com/josegonzalez/python-github-backup).

<!-- Keep this separator: Quarto otherwise moves the generated preamble below the following heading. -->

# Installing

## Basic install

Install with pip:

`pip3 install 'ghexport[export,dal,optional] @ git+https://github.com/karlicoss/ghexport'`

The
[‘extras’](https://packaging.python.org/en/latest/tutorials/installing-packages/#installing-extras)
in square brackets provide additional dependencies, feel free to omit
some of them if you don’t need it:

- `export` is needed for [export functionality](#exporting)
- `dal` is needed to [access exported data](#using-the-data)
- `optional` is for nicer logging facilities and faster JSON processing

See [`optional-dependencies`](pyproject.toml) section in
`pyproject.toml` for more details.

## Advanced install options

- editable install

  You’ll need to clone the repository with submodules.

  - use `git clone --recursive`, or
    `git pull && git submodule update --init`
  - after that, you can use `pip3 install --editable`

- run via `uvx`

  This allows you to run ghexport without installing if you just want to
  quickly try it out. E.g.:

  `uvx --from 'ghexport[export,dal,optional] @ git+https://github.com/karlicoss/ghexport' python3 -m ghexport.export ...`

  It’s a little awkward though since you can’t install tools without
  ‘executable scripts’ with uv at the moment.

# Exporting

## Running export

Usage:

**Recommended**: create `secrets.py` keeping your API parameters, e.g.:

    token = "TOKEN"

After that, use:

    python3 -m ghexport.export --secrets /path/to/secrets.py

That way you type less and have control over where you keep your
plaintext secrets.

**Alternatively**, you can pass parameters directly, e.g.

    python3 -m ghexport.export --token <token>

However, this is verbose and prone to leaking your keys/tokens/passwords
in shell history.

You can also import `ghexport.export` as a module and call `get_json`
function directly to get raw JSON.

I **highly** recommend checking exported files at least once just to
make sure they contain everything you expect from your export. If they
don’t, please feel free to ask or raise an issue!

## Setting up API parameters

To use the API, you need to get a [personal access
token](https://github.com/settings/tokens) from settings. Note that you
need to use the `repo` scope.

## Extra export options

- You can control specific data you want to export via the `--include`
  option (see `--help` for available fields).

  By default, all data will be included in the export.

- You can include or exclude [repository
  traffic](https://docs.github.com/en/rest/metrics/traffic) data via
  `--include-repos-traffic` or `--exclude-repos-traffic`.

  Currently it’s included by default.

  You might want to exclude it if you have some issues with the traffic
  API endpoint (it tends to be flakier than other endpoints).

# API limitations

**WARNING**: GitHub API limits the extent to which you can retrieve
certain data. For example,
[events](https://developer.github.com/v3/activity/events) are limited to
the past 90 days and no more than 300 events.

I **highly** recommend exporting regularly and keeping old exports. An
easy way to achieve it is a command like this:

    python3 -m ghexport.export --secrets /path/to/secrets.py >"export-$(date -I).json"

Or, you can use [arctee](https://github.com/karlicoss/arctee), which
automates this.

To get your older data past 90 days, you can request a [manual
export](https://github.com/settings/admin) in your account settings.

<!-- TODO hmm, mention that dal.py can handle this? -->

# Known Issues

The `requests` (and therefore `PyGithub`) modules on which this depends
seem to sometimes fail to log in if a `~/.netrc` file is present. See
[this
issue](https://github.com/psf/requests/issues/5801#issuecomment-901610012)
for context.

# Using the data

You can use `ghexport.dal` (stands for “Data Access/Abstraction Layer”)
to access your exported data, even offline. I elaborate on motivation
behind it [here](https://beepb00p.xyz/exports.html#dal).

- the main use case is importing it as a Python module for
  **programmatic access** to your data.

  You can find some inspiration in
  [`my.`](https://beepb00p.xyz/mypkg.html) package that I’m using as an
  API to all my personal data.

- to test it against your export, simply run:
  `python3 -m ghexport.dal --source /path/to/export`

- you can also try it interactively in an IPython shell:
  `python3 -m ghexport.dal --source /path/to/export --interactive`

## Example output

    Your events:
    Counter({'PushEvent': 181,
             'WatchEvent': 27,
             'CreateEvent': 22,
             'IssueCommentEvent': 20,
             'PullRequestEvent': 15,
             'IssuesEvent': 5,
             'DeleteEvent': 5,
             'ForkEvent': 3,
             'PullRequestReviewCommentEvent': 1})

# Contributing

If you want to contribute/develop this project, check out [github
actions](.github/workflows/main.yml) to see how the project is
run/tested.

Generally you should be able to run various checks via `tox`, e.g.

`uv tool run --with tox-uv tox`

## Updating README

This README is generated from a ‘literate’ Quarto
[README.qmd](README.qmd) via the following command:

`tox -e quarto`

If you want to correct something, feel free to simply update `README.md`
though, I can reconcile the changes next time I regenerate it.
