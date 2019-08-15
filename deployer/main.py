import click
from decouple import config

from .core import start_deployment, CoreException

# from .cleaner import start_cleaning


def _current_user():
    import getpass

    return getpass.getuser()


DEFAULT_MASTER_BRANCH = config("DEPLOYER_DEFAULT_MASTER_BRANCH", "master")
DEFAULT_UPSTREAM_NAME = config("DEPLOYER_DEFAULT_UPSTREAM_NAME", "origin")
DEFAULT_YOUR_REMOTE_NAME = config("DEPLOYER_DEFAULT_YOUR_REMOTE_NAME", _current_user())


# @click.command()
# @click.option(
#     "--master-branch",
#     default=DEFAULT_MASTER_BRANCH,
#     help=f"name of main branch (default {DEFAULT_MASTER_BRANCH!r})",
# )
# @click.option(
#     "--upstream-name",
#     default=DEFAULT_UPSTREAM_NAME,
#     help=f"name of upstream remote (default {DEFAULT_UPSTREAM_NAME!r})",
# )
# @click.option(
#     "--your-remote-name",
#     default=DEFAULT_YOUR_REMOTE_NAME,
#     help=f"Name of your remote (default {DEFAULT_YOUR_REMOTE_NAME!r})",
# )
# @click.argument("kumarepo")
# def cli(kumarepo, master_branch, upstream_name, your_remote_name):
#     config = {
#         "upstream_name": upstream_name,
#         "master_branch": master_branch,
#         "your_remote_name": your_remote_name,
#     }
#     try:
#         start_deployment(kumarepo, config)
#     except CoreException as exception:
#         info_out(exception.__class__.__name__)
#         error_out(str(exception))
#         raise click.Abort


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
    # click.echo("Debug mode is %s" % ("on" if debug else "off"))
    # pass


@cli.command()
@click.pass_context
def clean(ctx, kumarepo):
    click.echo(f"Clean {kumarepo}!!")


@cli.command()
# @click.argument("kumarepo")
@click.pass_context
def deploy(ctx):
    print(ctx)
    kumarepo = ctx.obj["kumarepo"]
    print("OPTIONS:", ctx.obj)
    click.echo(f"Deploy {kumarepo}!!")


# XXX DRY on these in core.py
def error_out(msg):
    click.echo(click.style(msg, fg="red"))


def info_out(msg):
    click.echo(click.style(msg, fg="yellow"))
