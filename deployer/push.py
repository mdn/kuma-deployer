from urllib.parse import urlparse

import git

from .exceptions import DirtyRepoError, PushBranchError, RemoteURLError
from .utils import info, success
from .constants import STAGE_PUSH_BRANCH, STAGE_INTEGRATIONTEST_BRANCH


def stage_push(repo_location, config):
    repo = git.Repo(repo_location)
    # Check if it's dirty
    if repo.is_dirty():
        raise DirtyRepoError(
            'The repo is currently "dirty". Stash or commit away.\n'
            f"Run `git status` inside {repo_location} to see what's up."
        )

    # Kuma
    _push(repo, config, STAGE_PUSH_BRANCH)
    success(
        f"Kuma: "
        f"Latest {STAGE_PUSH_BRANCH} branch pushed to {config['upstream_name']}"
    )

    # Kumascript
    ks_repo = repo.submodules["kumascript"].module()
    # just in case it was detached
    ks_repo.heads[config["master_branch"]].checkout()
    ks_remote = ks_repo.remotes[config["upstream_name"]]
    for url in ks_remote.urls:
        if "git://" in url:
            parsed = urlparse(url)
            better_url = f"git@{parsed.netloc}:{parsed.path[1:]}"
            raise RemoteURLError(
                f"Won't be able to push to {url}. Run something like:\n"
                f"\n\tcd kumascript\n"
                f"\tgit remote set-url {config['upstream_name']} {better_url}\n"
            )
    _push(ks_repo, config, STAGE_PUSH_BRANCH)
    success(
        f"Kumascript: "
        f"Latest {STAGE_PUSH_BRANCH} branch pushed to {config['upstream_name']}"
    )

    info("\nNow, check out: https://whatsdeployed.io/s/HC0/mozilla/kuma")
    info("And: https://whatsdeployed.io/s/SWJ/mdn/kumascript")

    # Now do the 'stage-integration-tests' too for Kuma
    _push(repo, config, STAGE_INTEGRATIONTEST_BRANCH)
    success(
        "Kumas: "
        f"Latest {STAGE_INTEGRATIONTEST_BRANCH} branch "
        f"pushed to {config['upstream_name']}"
    )

    info(
        "\nNow sit back and hold out for some sweat success of the integration tests."
        # XXX This should be "#mdn-dev on Slack instead"! Ed?
        "Check out #mdndev to for the joyous announcements."
    )
    info(
        "\nYou can also check out the results by visiting:\n\t"
        "https://ci.us-west-2.mdn.mozit.cloud/blue/organizations/jenkins/kuma/branches/"
    )


def _push(repo, config, branch_name):
    upstream_remote = repo.remotes[config["upstream_name"]]
    upstream_remote.fetch()

    active_branch = repo.active_branch
    if active_branch.name != branch_name:
        if branch_name not in [head.name for head in repo.heads]:
            stage_branch = repo.create_head(branch_name)

        else:
            for head in repo.heads:
                if head.name == branch_name:
                    stage_branch = head
                    break
            else:
                raise PushBranchError(f"Can't check out branch {branch_name!r}")

        stage_branch.checkout()

    # Merge the origin master branch into this
    origin_master_branch = f"{config['upstream_name']}/{config['master_branch']}"
    repo.git.merge(origin_master_branch)
    repo.git.push(config["upstream_name"], branch_name)

    # Back to master branch
    repo.heads[config["master_branch"]].checkout()
