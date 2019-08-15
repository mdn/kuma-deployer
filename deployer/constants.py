import getpass

from decouple import config


def _current_user():
    return getpass.getuser()


DEFAULT_MASTER_BRANCH = config("DEPLOYER_DEFAULT_MASTER_BRANCH", "master")
DEFAULT_UPSTREAM_NAME = config("DEPLOYER_DEFAULT_UPSTREAM_NAME", "origin")
DEFAULT_YOUR_REMOTE_NAME = config("DEPLOYER_DEFAULT_YOUR_REMOTE_NAME", _current_user())
