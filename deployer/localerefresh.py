import re
import os
import shlex
import subprocess
import datetime
import sys
import time
from pathlib import Path

import click
import git

from .submodules import make_submodules_pr
from .utils import info, success, warning, humanize_seconds
from .exceptions import (
    PuenteVersionError,
    DirtyRepoError,
    MasterBranchError,
    SubmoduleFindingError,
)


def run_command(command):
    process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)
    while True:
        output = process.stdout.readline()
        if output == "" and process.poll() is not None:
            break
        if output:
            print(output.strip())
    rc = process.poll()
    return rc


puente_version_regex = re.compile(r'([\'"]VERSION[\'"]:\s*[\'"]([\d\.]+)[\'"])')


def start_localerefresh(repo_location, config):
    repo = git.Repo(repo_location)

    if 0:
        raise NotImplementedError(
            "Need to check that your remote URL is: "
            "git remote set-url origin git@github.com:mozilla-l10n/mdn-l10n.git"
        )

    # Check if it's dirty
    if repo.is_dirty():
        raise DirtyRepoError(
            'The repo is currently "dirty". Stash or commit away.\n'
            f"Run `git status` inside {repo_location} to see what's up.\n"
            "Or, perhaps run 'git submodule update'"
        )

    # Are you on the "master" branch?
    active_branch = repo.active_branch
    if active_branch.name != config["master_branch"]:
        raise MasterBranchError(
            f"You first need to be on the {config['master_branch']!r} branch. "
            f"You're currently on the {active_branch.name!r} branch."
        )

    settings_file = Path(repo_location) / "kuma" / "settings" / "common.py"
    next_puente_version = None
    with open(settings_file) as f:
        kuma_settings_content = f.read()
        for __, found in puente_version_regex.findall(kuma_settings_content):
            year, increment = [int(x) for x in found.split(".")]
            current_year = datetime.datetime.utcnow().year
            if year != current_year:
                # First one of the new year!
                next_puente_version = f"{current_year}.01"
            else:
                next_puente_version = f"{year}.{increment + 1:<2}"
            info(
                f"Current PUENTE version: {found} - "
                f"Next PUENTE version: {next_puente_version}"
            )

    if not next_puente_version:
        raise PuenteVersionError("Can't find existing PUENTE version")

    locale_repo = repo.submodules["locale"].module()
    # Check out the master branch inside the 'locale' submodule
    # locale_repo.heads[config["master_branch"]].checkout()
    locale_repo.heads["master"].checkout()
    for remote in locale_repo.remotes:
        if remote.name == "origin":
            break
    else:
        raise SubmoduleFindingError(f"Can't find origin 'origin'")
    remote.pull(config["master_branch"])

    cmd = "docker-compose exec web make localerefresh"

    filename = "localerefresh.log"
    info(f"Hold my 🍺 whilst I run {cmd!r} (logging in {filename} too)")
    t0 = time.time()

    with open(filename, "wb") as f:  # replace 'w' with 'wb' for Python 3
        process = subprocess.Popen(
            shlex.split(cmd), stdout=subprocess.PIPE, cwd=repo_location
        )
        for line in iter(process.stdout.readline, b""):
            sys.stdout.write(line.decode("utf-8"))
            f.write(line)

    t1 = time.time()

    seconds = int(t1 - t0)
    success(
        f"Sucessfully ran localerefresh. "
        f"Only took {seconds % 3600 // 60} minutes, {seconds % 60} seconds."
    )

    new_msgids = set()
    total_diff_files = 0
    total_diff_lines = 0
    for diff in locale_repo.index.diff(None, create_patch=True):
        total_diff_files += 1
        for line in diff.diff.splitlines():
            total_diff_lines += 1
            if line.startswith(b"+msgid") and line != b'+msgid ""':
                new_msgids.add(line)

    info(f"{total_diff_files:,} files and {total_diff_lines:,} lines in the diff")

    if new_msgids:
        info(f"There are {len(new_msgids)} new '+msgid' strings.")
        if click.confirm("Wanna see a list of these new additions?", default=True):
            for line in new_msgids:
                info(f"\t{line.decode('utf-8')}")
    print("")  # Some whitespace
    if not click.confirm(
        "Do you want to proceed and commit this diff?", default=bool(new_msgids)
    ):
        info("Fine! Be like that!")
        info("To reset all changes to the submodules run:")
        info("\tgit submodule foreach git reset --hard")
        return

    # Gather all untracked files
    all_untracked_files = {}
    for path in locale_repo.untracked_files:
        path = os.path.join(locale_repo.working_dir, path)
        root = path.split(os.path.sep)[0]
        if root not in all_untracked_files:
            all_untracked_files[root] = {
                "files": [],
                "total_count": count_files_in_directory(root),
            }
        all_untracked_files[root]["files"].append(path)
    # Now filter this based on it being single files or a bunch
    untracked_files = {}
    for root, data in all_untracked_files.items():
        for path in data["files"]:
            age = time.time() - os.stat(path).st_mtime
            # If there's fewer untracked files in its directory, suggest
            # the directory instead.
            if data["total_count"] == 1:
                path = root
            if path in untracked_files:
                if age < untracked_files[path]:
                    # youngest file in that directory
                    untracked_files[path] = age
            else:
                untracked_files[path] = age

    if untracked_files:
        ordered = sorted(untracked_files.items(), key=lambda x: x[1], reverse=True)
        warning("There are untracked files in the locale submodule")
        for path, age in ordered:
            if os.path.isdir(path):
                path = path + "/"
            print("\t", path.ljust(60), humanize_seconds(age), "old")

        if not click.confirm("Wanna ignore those?", default=True):
            info("Go ahead and address those untracked files.")
            return

    # Now we're going to do the equivalent of `git commit -a -m "..."`
    index = locale_repo.index
    files_added = []
    files_removed = []
    for x in locale_repo.index.diff(None):
        if x.deleted_file:
            files_removed.append(x.b_path)
        else:
            files_added.append(x.b_path)
    files_new = []
    for x in locale_repo.index.diff(locale_repo.head.commit):
        files_new.append(x.b_path)
    if files_added:
        index.add(files_added)
        print("ADD", files_added)
    if files_removed:
        index.remove(files_removed)

    msg = f"Update strings {next_puente_version}"
    msg += "\n\n"
    msg += "New strings are as follows:\n"
    for line in new_msgids:
        msg += f"\t{line.decode('utf-8')}\n"
    # Do it like this (instead of `repo.git.commit(msg)`)
    # so that git signing works.
    locale_repo.git.commit(["--no-verify", "-m", msg])
    success("Committed 'locale' changes with the following commit message:")
    info(msg)

    # Now, push to the origin
    locale_repo.git.push("origin", "master")

    def next_puente_version_replacer(match):
        return match.group().replace(match.groups()[1], next_puente_version)

    new_kuma_settings_content = puente_version_regex.sub(
        next_puente_version_replacer, kuma_settings_content
    )
    assert new_kuma_settings_content != kuma_settings_content
    with open(settings_file, "w") as f:
        f.write(new_kuma_settings_content)
        success(f"Editing {settings_file} for {next_puente_version!r}")

    sha = locale_repo.head.object.hexsha
    short_sha = locale_repo.git.rev_parse(sha, short=7)

    make_submodules_pr(
        repo_location,
        config,
        accept_dirty=True,
        branch_name=f"locale-update-{next_puente_version}-{short_sha}",
        only_submodules=("locale",),
    )


def count_files_in_directory(directory):
    count = 0
    for root, _, files in os.walk(directory):
        # We COULD crosscheck these files against the .gitignore
        # if we ever felt overachievious.
        count += len(files)
    return count
