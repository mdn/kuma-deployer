import getpass

from decouple import config


def _current_user():
    return getpass.getuser()


GITHUB_ACCESS_TOKEN = config("GITHUB_ACCESS_TOKEN")
KUMA_REPO_NAME = config("DEPLOYER_KUMA_REPO_NAME", "mozilla/kuma")  # about to change!

DEFAULT_MASTER_BRANCH = config("DEPLOYER_DEFAULT_MASTER_BRANCH", "master")
DEFAULT_UPSTREAM_NAME = config("DEPLOYER_DEFAULT_UPSTREAM_NAME", "origin")
DEFAULT_YOUR_REMOTE_NAME = config("DEPLOYER_DEFAULT_YOUR_REMOTE_NAME", _current_user())

# DOCKERHUB_KUMA_TAGS_URL = config(
#     "DEPLOYER_DOCKERHUB_KUMA_TAGS_URL", "https://hub.docker.com/r/mdnwebdocs/kuma/tags"
#     "DEPLOYER_DOCKERHUB_KUMA_TAGS_URL",
#     # "https://hub.docker.com/v2/mdnwebdocs/kuma/tags/list",
#     # "https://registry.hub.docker.com/v2/mdnwebdocs/kuma/tags/list",
#     "https://registry.hub.docker.com/v2/repositories/mdnwebdocs/kuma/tags/",
# )
