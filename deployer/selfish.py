import re

import git
from github import Github

from .constants import GITHUB_ACCESS_TOKEN, KUMA_REPO_NAME
from .exceptions import DirtyRepoError
from .utils import success, warning


def self_check(repo_location, config):
    repo = git.Repo(repo_location)
    if repo.is_dirty():
        raise DirtyRepoError(
            'The repo is currently "dirty". Stash or commit away.\n'
            f"Run `git status` inside {repo_location} to see what's up."
        )
    success(f"Repo at {repo_location} is not dirty.")

    for submodule in repo.submodules:
        submodule.update(init=True)
        sub_repo = submodule.module()
        if sub_repo.is_dirty():
            raise DirtyRepoError(f"The git submodule {submodule!r} is dirty.")
        success(f"Git submodule {submodule.name!r} is not dirty.")

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
