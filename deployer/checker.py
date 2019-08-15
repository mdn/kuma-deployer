import git
import requests

from .utils import warning, info, success
from .exceptions import MasterBranchError


def check_builds(repo_location, config):
    repo = git.Repo(repo_location)
    # Are you on the "master" branch?
    active_branch = repo.active_branch
    if active_branch.name != config["master_branch"]:
        raise MasterBranchError(
            f"You first need to be on the {config['master_branch']!r} branch. "
            f"You're currently on the {active_branch.name!r} branch."
        )

    # Check Kuma
    sha = repo.head.object.hexsha
    short_sha = repo.git.rev_parse(sha, short=7)
    info(f"Looking for Kuma short sha {short_sha}")
    public_url = "https://hub.docker.com/r/mdnwebdocs/kuma/tags"
    api_url = "https://registry.hub.docker.com/v2/repositories/mdnwebdocs/kuma/tags/"
    response = requests.get(api_url)
    response.raise_for_status()
    published_shas = [result["name"] for result in response.json()["results"]]
    if short_sha in published_shas:
        success(f"Kuma sha {short_sha} is on {public_url}")
    else:
        warning(f"Could not find {short_sha} on {public_url} :(")

    # Check Kumascript
    ks_repo = repo.submodules["kumascript"].module()
    sha = ks_repo.head.object.hexsha
    ks_short_sha = ks_repo.git.rev_parse(sha, short=7)
    info(f"Looking for Kumascript short sha {ks_short_sha}")
    public_url = "https://hub.docker.com/r/mdnwebdocs/kumascript/tags"
    api_url = (
        "https://registry.hub.docker.com/v2/repositories/mdnwebdocs/kumascript/tags/"
    )
    response = requests.get(api_url)
    response.raise_for_status()
    published_shas = [result["name"] for result in response.json()["results"]]
    if ks_short_sha in published_shas:
        success(f"Kumascript sha {ks_short_sha} is on {public_url}")
    else:
        warning(f"Could not find {ks_short_sha} on {public_url} :(")

    print("")

    # Check Kuma on Jenkins
    url = (
        "https://ci.us-west-2.mdn.mozit.cloud"
        "/blue/organizations/jenkins/kuma/activity/?branch=master"
    )
    info("Jenkins is both auth and VPN protected. Visit this URL and ...")
    info(f"Look for:  {short_sha}   on:")
    info(url)
    if input("Was it there? [Y/n] ").lower().strip() not in ("y", ""):
        warning("Hmm... Not sure what to think about that. Try in a couple of minutes?")
        return
    success("Great!\n")

    # Check Kuma on Jenkins
    url = (
        "https://ci.us-west-2.mdn.mozit.cloud"
        "/blue/organizations/jenkins/kumascript/activity/?branch=master"
    )
    info("Jenkins is both auth and VPN protected. Visit this URL and ...")
    info(f"Look for:  {ks_short_sha}   on:")
    info(url)
    if input("Was it there? [Y/n] ").lower().strip() not in ("y", ""):
        warning("Hmm... Not sure what to think about that. Try in a couple of minutes?")
        return
    success("Great!\nThere is hope in this world!")
