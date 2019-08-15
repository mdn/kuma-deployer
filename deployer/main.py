import functools

import click

from .core import start_deployment, CoreException
from .cleaner import start_cleaner
from .utils import error, info
from .constants import (
    DEFAULT_MASTER_BRANCH,
    DEFAULT_UPSTREAM_NAME,
    DEFAULT_YOUR_REMOTE_NAME,
)


def cli_wrap(fn):
    @functools.wraps(fn)
    def inner(*args, **kwargs):
        try:
            fn(*args, **kwargs)
        except CoreException as exception:
            info(exception.__class__.__name__)
            error(str(exception))
            raise click.Abort

    return inner


start_deployment = cli_wrap(start_deployment)
start_cleaner = cli_wrap(start_cleaner)


@click.group()
@click.option(
    "--master-branch",
    default=DEFAULT_MASTER_BRANCH,
    help=f"name of main branch (default {DEFAULT_MASTER_BRANCH!r})",
)
@click.option(
    "--upstream-name",
    default=DEFAULT_UPSTREAM_NAME,
    help=f"name of upstream remote (default {DEFAULT_UPSTREAM_NAME!r})",
)
@click.option(
    "--your-remote-name",
    default=DEFAULT_YOUR_REMOTE_NAME,
    help=f"Name of your remote (default {DEFAULT_YOUR_REMOTE_NAME!r})",
)
@click.option("--debug/--no-debug", default=False)
@click.argument("kumarepo")
@click.pass_context
def cli(ctx, kumarepo, debug, master_branch, upstream_name, your_remote_name):
    ctx.ensure_object(dict)
    ctx.obj["kumarepo"] = kumarepo
    ctx.obj["debug"] = debug
    ctx.obj["master_branch"] = master_branch
    ctx.obj["upstream_name"] = upstream_name
    ctx.obj["your_remote_name"] = your_remote_name


@cli.command()
@click.pass_context
def clean(ctx):
    kumarepo = ctx.obj["kumarepo"]
    start_cleaner(kumarepo, ctx.obj)


@cli.command()
@click.pass_context
def deploy(ctx):
    kumarepo = ctx.obj["kumarepo"]
    start_deployment(kumarepo, ctx.obj)
