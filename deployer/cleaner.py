import git
from github import Github, GithubException

from .constants import GITHUB_ACCESS_TOKEN, KUMA_REPO_NAME
from .exceptions import DirtyRepoError
from .utils import info, success, warning


def start_cleaner(repo_location, config):
    repo = git.Repo(repo_location)
    # Check if it's dirty
    if repo.is_dirty():
        raise DirtyRepoError(
            'The repo is currently "dirty". Stash or commit away.\n'
            f"Run `git status` inside {repo_location} to see what's up."
        )

    # XXX I'd like to move away from branches and switch to tags.
    # But for now, just to check sanity do a-something.
    active_branch = repo.active_branch
    if active_branch.name.startswith("pre-push"):
        # Find its pull request and see if it's merged
        g = Github(GITHUB_ACCESS_TOKEN)
        g_repo = g.get_repo(KUMA_REPO_NAME)

        pulls = g_repo.get_pulls(
            sort="created",
            direction="desc",
            state="closed",
            head=active_branch.name,
            base="master",
        )
        raise NotImplementedError("this doesn't work.")
        # Seems it always returns everything
        for pr in pulls:
            print(pr.number, pr.title, pr.head.ref, pr.base.ref, pr.merged)
            # print(dir(pr))
            # break
