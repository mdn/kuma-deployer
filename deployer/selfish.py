import re
import os

import git
from github import Github

from .constants import GITHUB_ACCESS_TOKEN, KUMA_REPO_NAME
from .exceptions import DirtyRepoError
from .utils import success, warning, info


def self_check(repo_location, config):
    def pp_location(p):
        """return the location if displayed using the ~ notation
        for the user's home directory."""
        home_dir = os.path.expanduser("~")
        if p.startswith(home_dir):
            return p.replace(home_dir, "~")
        return p

    info("Current config...")
    for k in sorted(config):
        info(f"{k:<30}: {config[k]}")
    print()  # whitespace

    repo = git.Repo(repo_location)

    expect_remote_names = [config["upstream_name"], config["your_remote_name"]]
    for remote in repo.remotes:
        if remote.name in expect_remote_names:
            success(f"{pp_location(repo_location)} has a remote called {remote.name}")
            expect_remote_names.remove(remote.name)

    for name in expect_remote_names:
        warning(f"Warning! Couldn't find a remote named {name!r}")

    print()  # whitespace

    if repo.is_dirty():
        raise DirtyRepoError(
            'The repo is currently "dirty". Stash or commit away.\n'
            f"Run `git status` inside {pp_location(repo_location)} to see what's up."
        )
    success(f"Repo at {pp_location(repo_location)} is not dirty.")
    print()  # whitespace

    for submodule in repo.submodules:
        submodule.update(init=True)
        sub_repo = submodule.module()
        if sub_repo.is_dirty():
            raise DirtyRepoError(f"The git submodule {submodule!r} is dirty.")
        success(f"Git submodule {submodule.name!r} is not dirty.")

        # Check that it has remote named {submodules_upstream_name}
        for remote in sub_repo.remotes:
            if remote.name == config["submodules_upstream_name"]:
                break
        else:
            warning(
                f"The git submodule {submodule.name!r} does not have a remote "
                f"called {config['submodules_upstream_name']!r}!"
            )

    g = Github(GITHUB_ACCESS_TOKEN)
    g_repo = g.get_repo(KUMA_REPO_NAME)
    pulls = g_repo.get_pulls(
        sort="created", direction="desc", state="open", base="master"
    )
    for pr in pulls:
        if (
            pr.title.startswith("Submodules: ")
            and re.findall(r"[a-f0-9]{7}\.\.\.[a-f0-9]{7}", pr.title)
            and pr.state != "closed"
        ):
            warning(f"Appears to have open pull request to update submodules! {pr.url}")
            break

    # XXX What else can we check? What about having access to Jenkins?
