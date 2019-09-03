# kuma-deployer

In the ancient times of roaming saber tooth tigers and the smog over London
hanging deep there was a time the poor serfs of Kuma had to trudge through
[https://kuma.readthedocs.io/en/latest/deploy.html](https://kuma.readthedocs.io/en/latest/deploy.html)
like some Kafkaesque slave of the man. That was then. This is now.

Everything that can be automated in the Kuma deploy process is scripted here.

## Limitations and caveats

**Hopefully, all temporary limitations and caveats.**

There are some things that are hard to do such as pulling information out of Jenkins
since it requires authentication and VPN.

The other thing is that all the current commands are independent and users need to
know which order to run them. Ideally, it should all be wrapped up into one single
command but that's a little bit tricky since it requires waiting and external
checking.

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

NOTE! The `.env` file (with the `GITHUB_ACCESS_TOKEN`) needs to be in the
_current working directory_. I.e. where you are when you run `kuma-deployer`. So
not necessarily where your `kuma` directory is (if these two are different).

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

All of the code style stuff can be simplified by installing `therapist`. It should
get installed by default, but setting it up as a `git` `pre-commit` hook is optional.
Here's how you set it up once:

    therapist install

Now, next time you try to commit a `.py` file with a `black` or `flake8` violation
it will remind you and block the commit. You can override it like this:

    git commit -a -m "I know what I'm doing"

To run _all_ code style and lint checkers you can also use `therapist` with:

    therapist run --use-tracked-files

Some things can't be automatically fixed, but `black` violations can for example:

    therapist run --use-tracked-files --fix

## Contributing and using

If you like to use the globally installed executable `kuma-deployer` but don't want
to depend on a new PyPI release for every change you want to try, use this:

    # If you use a virtualenv, deactivate it first
    deactive
    # Use the global pip (or pip3) on your system
    pip3 install -e .

If you do this, you can use this repo to install in your system.
