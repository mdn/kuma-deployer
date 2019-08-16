import getpass

from decouple import config


def _current_user():
    return getpass.getuser()


GITHUB_ACCESS_TOKEN = config("GITHUB_ACCESS_TOKEN")
KUMA_REPO_NAME = config("DEPLOYER_KUMA_REPO_NAME", "mozilla/kuma")  # about to change!

DEFAULT_MASTER_BRANCH = config("DEPLOYER_DEFAULT_MASTER_BRANCH", "master")
DEFAULT_UPSTREAM_NAME = config("DEPLOYER_DEFAULT_UPSTREAM_NAME", "origin")
DEFAULT_YOUR_REMOTE_NAME = config("DEPLOYER_DEFAULT_YOUR_REMOTE_NAME", _current_user())

WHATSDEPLOYED_URL = config(
    "DEPLOYER_WHATSDEPLOYED_URL", "https://whatsdeployed.io/s/HC0/mozilla/kuma"
)
STAGE_PUSH_BRANCH = config("DEPLOYER_STAGE_PUSH_BRANCH", "stage-push")
STAGE_INTEGRATIONTEST_BRANCH = config(
    "DEPLOYER_STAGE_INTEGRATIONTEST_BRANCH", "stage-integration-tests"
)
PROD_PUSH_BRANCH = config("DEPLOYER_PROD_PUSH_BRANCH", "prod-push")
STANDBY_PUSH_BRANCH = config("DEPLOYER_STANDBY_PUSH_BRANCH", "standby-push")
