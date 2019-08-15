import datetime

import click
import git
from decouple import config
from github import Github, GithubException

GITHUB_ACCESS_TOKEN = config("GITHUB_ACCESS_TOKEN")
KUMA_REPO_NAME = config("DEPLOYER_KUMA_REPO_NAME", "mozilla/kuma")  # about to change!


def warning(*msg):
    msg = " ".join([str(x) for x in msg])
    click.echo(click.style(msg, fg="yellow"))


def info(*msg):
    msg = " ".join([str(x) for x in msg])
    click.echo(click.style(msg))


def success(*msg):
    msg = " ".join([str(x) for x in msg])
    click.echo(click.style(msg, fg="green"))


class CoreException(Exception):
    """Exists for the benefit of making the cli easier to catch exceptions."""


# class GitCloneError(CoreException):
#     """When struggling to do the git clone thing."""


class SubmoduleFindingError(CoreException):
    """when struggling to find the submodule."""


# class PullRequestError(CoreException):
#     """when struggling to find, edit, or make pull request."""


# class NothingToUpdateError(CoreException):
#     """when you discover the submodule is totally up-to-date already."""


class DirtyRepoError(CoreException):
    """dirty repo, d'uh"""


class MasterBranchError(CoreException):
    """Not on the right branch"""


def start_deployment(repo_location, config):
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
    branch_name = default_name = f"pre-push-{now.strftime('%Y-%m-%d')}"

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
            g_repo = g.get_repo("mozilla/kuma")

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
        # return created_pr


# print(submodules)
# for submodule in submodules:
#     short_sha = sub_repo.git.rev_parse(sha, short=7)

# print(dir(repo))
# submodules = {}


# def make_prs(org, repo, config):
#     clone_url = f"git@github.com:{org}/{repo}.git"
#     name = repo
#     config["repo_name"] = f"{org}/{repo}"
#     with tempfile.TemporaryDirectory() as tmpdir:
#         destination = Path(tmpdir) / name
#         cmd = f"git clone --depth=50 {clone_url} {destination}".split()
#         completed_process = subprocess.run(cmd, capture_output=True)
#         if completed_process.returncode:
#             raise GitCloneError(completed_process.stderr.decode("utf-8"))
#         make_branch(destination, config)


# def make_branch(repo_path, config):
#     repo = git.Repo(repo_path)
#     submodules = {}
#     name = config.get("submodule_name")
#     for submodule in repo.submodules:
#         submodules[submodule.name] = submodule
#     if not submodules:
#         raise SubmoduleFindingError("No submodules found")
#     elif len(submodules) > 1 and not name:
#         raise SubmoduleFindingError(f"Found more than 1 ({submodule.keys()}")
#     elif not name:
#         submodule, = list(submodules.values())
#         name = submodule.name
#     else:
#         submodule = submodules[name]

#     submodule.update(init=True)
#     branch_name = config.get("submodule_branch") or "master"
#     origin_name = config.get("submodule_origin") or "origin"
#     sub_repo = submodule.module()
#     sub_repo.git.checkout(branch_name)
#     for remote in sub_repo.remotes:
#         if remote.name == origin_name:
#             break
#     else:
#         raise SubmoduleFindingError(f"Can't find origin {origin_name!r}")
#     sha = sub_repo.head.object.hexsha

#     short_sha = sub_repo.git.rev_parse(sha, short=7)
#     remote.pull(branch_name)
#     sha2 = sub_repo.head.object.hexsha
#     short_sha2 = sub_repo.git.rev_parse(sha2, short=7)

#     if sha == sha2:
#         raise NothingToUpdateError(f"Latest sha is already {sha}")

#     new_branch_name = f"update-{name}-{short_sha}-to-{short_sha2}"
#     print("New branch name", new_branch_name)

#     # Check that the branch and PR doesn't already exist
#     g = Github(GITHUB_ACCESS_TOKEN)
#     # Bail if we already have a PR by this branch name
#     repo_name = config["repo_name"]
#     g_repo = g.get_repo(repo_name)
#     if config["git_server"] != "github.com":
#         raise NotImplementedError
#     # pulls = repo.get_pulls(state='open', sort='created', base='master')
#     pulls = g_repo.get_pulls(sort="created", base="master")
#     for pull in pulls:
#         branch_ref_name = pull.raw_data["head"]["ref"]
#         if new_branch_name in branch_ref_name:
#             url = pull.raw_data["_links"]["html"]["href"]
#             raise PullRequestError(f"Already at a pull request at {url}")

#     current = repo.create_head(new_branch_name)
#     current.checkout()
#     repo.git.add(A=True)
#     msg = f"Update submodule {name!r} from {short_sha} to {short_sha2}"
#     repo.git.commit(["-m", msg])
#     pushed = repo.git.push("origin", new_branch_name)
#     print("PUSHED:")
#     print(repr(pushed))

#     # https://github.com/PyGithub/PyGithub/blob/6e79d2704b8812d26435b21c1258c766418ab25e/github/Repository.py#L1207
#     body = "Updating the submodule! 😊\n"
#     created_pr = g_repo.create_pull(msg, body, "master", new_branch_name)
#     print(created_pr.html_url)
#     return created_pr
