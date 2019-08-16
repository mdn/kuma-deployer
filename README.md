# kuma-deployer

In the ancient times of roaming saber tooth tigers and the smog over London
hanging deep there was a time the poor serfs of Kuma had to trudge through
[https://kuma.readthedocs.io/en/latest/deploy.html](https://kuma.readthedocs.io/en/latest/deploy.html)
like some Kafkaesque slave of the man. That was then. This is now.

Everything that can be automated in the Kuma deploy process is scripted here.

## Limitations and caveats

At the time of writing, **this is a prototype**. It's doing the least possible
to make the most basic thing work.

- start
- writing
- them
- here

## Getting started

You'll need a GitHub access token.
Go to [github.com/settings/tokens](https://github.com/settings/tokens) and create a token,
copy and paste it into your `.env` file or use `export`. E.g.

    cat .env
    GITHUB_ACCESS_TOKEN=a36f6736...

    pip install kuma-deployer
    kuma-deployer --help

If you don't use a `.env` file you can use:

    GITHUB_ACCESS_TOKEN=a36f6736... kuma-deployer --help

## Goal

The goal is that you simply install this script and type `kuma-deploy` and sit
back and relax and with a bit of luck MDN is fully upgraded, deployment, and enabled.

## Contributing

Clone this repo then run:

    pip install -e ".[dev]"

That should have installed the CLI `kuma-deployer`

    kuma-deployer --help

If you wanna make a PR, make sure it's formatted with `black` and passes `flake8`.

You can check that all files are `flake8` fine by running:

    flake8 deployer

And to check that all files are formatted according to `black` run:

    black --check deployer
