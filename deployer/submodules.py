import datetime

import git
from github import Github, GithubException

from .constants import GITHUB_ACCESS_TOKEN, KUMA_REPO_NAME
from .exceptions import DirtyRepoError, MasterBranchError, SubmoduleFindingError
from .utils import info, success, warning


def make_submodules_pr(repo_location, config):
    repo = git.Repo(repo_location)
    # Check if it's dirty
    if repo.is_dirty():
        raise DirtyRepoError(
            'The repo is currently "dirty". Stash or commit away.\n'
            f"Run `git status` inside {repo_location} to see what's up."
        )

    # Are you on the "master" branch?
    active_branch = repo.active_branch
    if active_branch.name != config[
        "master_branch"
    ] and not active_branch.name.startswith("pre-push"):
        raise MasterBranchError(
            f"You first need to be on the {config['master_branch']!r} branch. "
            f"You're currently on the {active_branch.name!r} branch."
        )

    now = datetime.datetime.utcnow()
    branch_name = f"pre-push-{now.strftime('%Y-%m-%d')}"

    # Come up with a pre-push branch name
    # existing_branch_names = [x.name for x in repo.heads]
    for head in repo.heads:
        if head.name == branch_name:
            print(f"Branch {head.name!r} already exists. Wanna re-use?")
            if input(f"Check out {head.name!r}? [y/N] ").lower() == "y":
                head.checkout()
                break
            else:
                raise NotImplementedError("Branch already exists and you don't want it")
    else:
        # Create the new branch
        new_branch = repo.create_head(branch_name)
        new_branch.checkout()

    # Check out all the latest and greatest submodules
    actual_updates = {}
    for submodule in repo.submodules:
        submodule.update(init=True)
        sub_repo = submodule.module()
        sub_repo.git.checkout(config["master_branch"])
        sha = sub_repo.head.object.hexsha
        short_sha = sub_repo.git.rev_parse(sha, short=7)
        for remote in sub_repo.remotes:
            if remote.name == config["upstream_name"]:
                break
        else:
            raise SubmoduleFindingError(
                f"Can't find origin {config['upstream_name']!r}"
            )
        remote.pull(config["master_branch"])

        sha2 = sub_repo.head.object.hexsha
        short_sha2 = sub_repo.git.rev_parse(sha2, short=7)

        if sha != sha2:
            info(f"Submodule {submodule.name!r} from {short_sha} to {short_sha2}")
            actual_updates[submodule.name] = [short_sha, short_sha2]
        else:
            warning(f"Submodule {submodule.name!r} already latest and greatest.")

    # actual_updates = {"kumascript": ["b70bab1", "9c29f10"]}

    if actual_updates:
        msg = f"Update submodule{'s' if len(actual_updates) > 1 else ''} "
        for name in sorted(actual_updates):
            shas = actual_updates[name]
            msg += f"{name} ({shas[0]} to {shas[1]}) "
        msg = msg.strip()
        info("About to commit with this message:", msg)
        repo.git.add(A=True)
        repo.git.commit(["-m", msg, "--no-verify"])
        pushed = repo.git.push(config["your_remote_name"], branch_name)
        print("PUSHED:", repr(pushed))

        try:
            g = Github(GITHUB_ACCESS_TOKEN)
            g_repo = g.get_repo(KUMA_REPO_NAME)

            # Would be cool if this could list the difference!
            body = "Updating the submodule! 😊\n"

            created_pr = g_repo.create_pull(msg, body, "master", branch_name)
            # print(created_pr.html_url)
            success(f"Now go and patiently wait for {created_pr.html_url} to go green.")

        except GithubException as exception:
            warning("GitHub integration failed:", exception)

            info("You can manually create the pull request:")
            create_pr_url = (
                f"https://github.com/{KUMA_REPO_NAME}/compare/master..."
                f"{config['your_remote_name']}:{branch_name}?expand=1"
            )
            success(f"\n\t{create_pr_url}\n")
