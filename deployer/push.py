import shutil
import time
from urllib.parse import urlparse

import click
import git

from .constants import (
    PROD_PUSH_BRANCH,
    STAGE_INTEGRATIONTEST_BRANCH,
    STAGE_PUSH_BRANCH,
    STANDBY_PUSH_BRANCH,
)
from .exceptions import (
    DirtyRepoError,
    PushBranchError,
    RemoteURLError,
    MasterBranchError,
)
from .utils import info, success, warning, requests_retry_session


def center(msg):
    t_width, _ = shutil.get_terminal_size(fallback=(80, 24))
    warning(f"-----  {msg}  ".ljust(t_width, "-"))


def stage_push(repo_location, config):
    center(f"STAGE {STAGE_PUSH_BRANCH!r}")
    push(repo_location, config, STAGE_PUSH_BRANCH)

    print("\n")  # some deliberate whitespace
    center(f"STAGE {STAGE_INTEGRATIONTEST_BRANCH!r}")
    push(repo_location, config, STAGE_INTEGRATIONTEST_BRANCH, show_whatsdeployed=False)
    info(
        "\nNow sit back and hold out for some sweat success of the integration tests. "
        "Check out #mdn-infra, on Slack, to for the joyous announcements. \n"
        "https://mozilla.slack.com/messages/CAVQJ18E6"
    )
    info(
        "\nYou can also check out the results by visiting:\n\t"
        "https://ci.us-west-2.mdn.mozit.cloud/blue/organizations/jenkins/kuma/branches/"
    )

    print("\n")  # deliberate whitespace
    start_watching_for_change("https://developer.allizom.org/media/revision.txt")


def prod_push(repo_location, config):
    center(f"PROD {PROD_PUSH_BRANCH!r}")
    push(repo_location, config, PROD_PUSH_BRANCH)

    info(
        "\nAfter Whatsdeploy says it's up, go troll and lurk on:\n\t"
        "https://rpm.newrelic.com/accounts/1807330/applications/"
        "72968468/traced_errors\n"
    )

    print("\n")  # some deliberate whitespace
    center(f"PROD {STANDBY_PUSH_BRANCH!r}")
    push(repo_location, config, STANDBY_PUSH_BRANCH)

    print("\n")  # deliberate whitespace
    start_watching_for_change("https://developer.mozilla.org/media/revision.txt")


def push(repo_location, config, branch, show_whatsdeployed=True, show_jenkins=True):
    repo = git.Repo(repo_location)
    # Check if it's dirty
    if repo.is_dirty():
        raise DirtyRepoError(
            'The repo is currently "dirty". Stash or commit away.\n'
            f"Run `git status` inside {repo_location} to see what's up."
        )

    # Are you on the "master" branch?
    active_branch = repo.active_branch
    if active_branch.name == config["master_branch"]:
        # Need to check that it's up to date.
        # But before that can be done we need to git fetch origin.
        upstream_remote = repo.remotes[config["upstream_name"]]
        info(f"Fetching all branches from {config['upstream_name']}")
        upstream_remote.fetch()
        remote_master_branch = f"{config['upstream_name']}/{config['master_branch']}"
        diff = repo.git.diff(remote_master_branch)
        if diff:
            warning(
                f"Your local {config['master_branch']} is different from "
                f"{remote_master_branch!r}."
            )
            if click.confirm(
                f"Want to pull latest {remote_master_branch!r}", default=True
            ):
                upstream_remote.pull(config["master_branch"])
                info(
                    f"Pulled latest {config['master_branch']} from "
                    f"{config['upstream_name']}."
                )
            else:
                warning("Godspeed!")
    else:
        msg = (
            f"You're not on the {config['master_branch']!r} branch. "
            f"You're on {active_branch.name!r}."
        )
        warning(msg)
        if not click.confirm("Are you sure you want to proceed?"):
            raise MasterBranchError(
                f"Bailing because not in {config['master_branch']!r}"
            )

    # Kuma
    short_sha = _push_repo(repo, config, branch)
    success(
        f"Kuma: " f"Latest {branch!r} branch pushed to {config['upstream_name']!r}\n"
    )
    if show_jenkins:
        sha = repo.head.object.hexsha
        short_sha = repo.git.rev_parse(sha, short=7)
        jenkins_url = (
            f"https://ci.us-west-2.mdn.mozit.cloud/blue/organizations/jenkins/"
            f"kuma/activity?branch={branch}"
        )
        info(f"Now, look for {short_sha} in\n\t{jenkins_url}")
    if show_whatsdeployed:
        info("Keep an eye on\n\thttps://whatsdeployed.io/s/HC0/mozilla/kuma")

    print("\n")  # Some whitespace before Kumascript

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
    short_sha = _push_repo(ks_repo, config, branch)
    success(
        f"Kumascript: "
        f"Latest {branch!r} branch pushed to {config['upstream_name']!r}"
    )
    if show_jenkins:
        jenkins_url = (
            f"https://ci.us-west-2.mdn.mozit.cloud/blue/organizations/jenkins/"
            f"kumascript/activity?branch={branch}"
        )
        info(f"Now, look for {short_sha} in\n\t{jenkins_url}")
    if show_whatsdeployed:
        info("Keep an eye on\n\thttps://whatsdeployed.io/s/SWJ/mdn/kumascript")


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
    sha = repo.head.object.hexsha
    short_sha = repo.git.rev_parse(sha, short=7)
    repo.git.push(config["upstream_name"], branch_name)

    # Back to master branch
    repo.heads[config["master_branch"]].checkout()

    return short_sha


def start_watching_for_change(url, sleep_seconds=10):
    session = requests_retry_session()
    response = session.get(url)
    response.raise_for_status()

    def fmt_seconds(delta):
        seconds = int(delta)
        if seconds > 60:
            minutes = seconds // 60
            seconds = seconds % 60
            return (
                f"{minutes} minute{'s' if minutes > 1 else ''} "
                f"{seconds} second{'s' if seconds > 1 else ''} "
            )
        return f"{seconds} second{'s' if seconds > 1 else ''} "

    t0 = time.time()
    first_content = response.text
    info(f"Watching for changes to output from {url}")
    print(f"(checking every {sleep_seconds} seconds)")
    while True:
        time.sleep(10)

        response = session.get(url)
        response.raise_for_status()
        new_content = response.text
        if new_content != first_content:
            success(f"Output from {url} has changed!\n")
            info(f"from {first_content!r} to {new_content!r}")
            info("Stopping the watcher. Bye!")
            break
        else:
            print(f"Been checking for {fmt_seconds(time.time() - t0)}")
