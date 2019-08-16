import shutil
from urllib.parse import urlparse

import git

from .constants import (
    PROD_PUSH_BRANCH,
    STAGE_INTEGRATIONTEST_BRANCH,
    STAGE_PUSH_BRANCH,
    STANDBY_PUSH_BRANCH,
)
from .exceptions import DirtyRepoError, PushBranchError, RemoteURLError
from .utils import info, success, warning


def center(msg):
    t_width, _ = shutil.get_terminal_size(fallback=(80, 24))
    warning(f"-----  {msg}  ".ljust(t_width, "-"))


def stage_push(repo_location, config):
    center(f"STAGE {STAGE_PUSH_BRANCH!r}")
    push(repo_location, config, STAGE_PUSH_BRANCH)

    print("\n")  # some deliberate whitespace
    center(f"STAGE {STAGE_PUSH_BRANCH!r}")
    push(repo_location, config, STAGE_INTEGRATIONTEST_BRANCH)
    info(
        "\nNow sit back and hold out for some sweat success of the integration tests."
        # XXX This should be "#mdn-dev on Slack instead"! Ed?
        "Check out #mdndev to for the joyous announcements."
    )
    info(
        "\nYou can also check out the results by visiting:\n\t"
        "https://ci.us-west-2.mdn.mozit.cloud/blue/organizations/jenkins/kuma/branches/"
    )


def prod_push(repo_location, config):
    center(f"PROD {PROD_PUSH_BRANCH!r}")
    push(repo_location, config, PROD_PUSH_BRANCH)

    info(
        "\nAfter Whatsdeploy says it's up, go troll and lurk on:\n"
        "\thttps://rpm.newrelic.com/accounts/1807330/applications/72968468/traced_errors\n"
    )

    print("\n")  # some deliberate whitespace
    center(f"PROD {STANDBY_PUSH_BRANCH!r}")
    push(repo_location, config, STANDBY_PUSH_BRANCH)


def push(repo_location, config, branch):
    repo = git.Repo(repo_location)
    # Check if it's dirty
    if repo.is_dirty():
        raise DirtyRepoError(
            'The repo is currently "dirty". Stash or commit away.\n'
            f"Run `git status` inside {repo_location} to see what's up."
        )

    # Kuma
    _push_repo(repo, config, branch)
    success(f"Kuma: " f"Latest {branch!r} branch pushed to {config['upstream_name']!r}")

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
    _push_repo(ks_repo, config, branch)
    success(
        f"Kumascript: "
        f"Latest {branch!r} branch pushed to {config['upstream_name']!r}"
    )

    info("\nNow, check out: https://whatsdeployed.io/s/HC0/mozilla/kuma")
    info("And: https://whatsdeployed.io/s/SWJ/mdn/kumascript")


def _push_repo(repo, config, branch_name):
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
