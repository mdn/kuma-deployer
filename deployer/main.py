import functools
from pathlib import Path

import click

from .checker import check_builds
from .cleaner import start_cleaner
from .constants import (
    DEFAULT_MASTER_BRANCH,
    DEFAULT_UPSTREAM_NAME,
    DEFAULT_YOUR_REMOTE_NAME,
)
from .exceptions import CoreException
from .localerefresh import start_localerefresh
from .push import prod_push, stage_push
from .submodules import make_submodules_pr
from .utils import error, info


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


# XXX This all feels clunky! Usefuly functionality but annoying to have to repeat
# the names so much.
make_submodules_pr = cli_wrap(make_submodules_pr)
start_cleaner = cli_wrap(start_cleaner)
start_localerefresh = cli_wrap(start_localerefresh)
check_builds = cli_wrap(check_builds)
stage_push = cli_wrap(stage_push)
prod_push = cli_wrap(prod_push)


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

    p = Path(kumarepo)
    if not p.exists():
        error(f"{kumarepo} does not exist")
        raise click.Abort
    if not (p / ".git").exists():
        error(f"{p / '.git'} does not exist so it's not a git repo")
        raise click.Abort


@cli.command()
@click.pass_context
def clean(ctx):
    start_cleaner(ctx.obj["kumarepo"], ctx.obj)


@cli.command()
@click.pass_context
def submodules(ctx):
    make_submodules_pr(ctx.obj["kumarepo"], ctx.obj)


@cli.command()
@click.pass_context
def l10n(ctx):
    start_localerefresh(ctx.obj["kumarepo"], ctx.obj)


@cli.command()
@click.pass_context
def checkbuilds(ctx):
    check_builds(ctx.obj["kumarepo"], ctx.obj)


@cli.command()
@click.pass_context
def stagepush(ctx):
    stage_push(ctx.obj["kumarepo"], ctx.obj)


@cli.command()
@click.pass_context
def prodpush(ctx):
    prod_push(ctx.obj["kumarepo"], ctx.obj)
