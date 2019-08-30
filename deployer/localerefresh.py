import shlex
import subprocess
import sys
import time

import click
import git

from .utils import info, success


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


def start_localerefresh(repo_location, config):
    repo = git.Repo(repo_location)
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
    locale_repo = repo.submodules["locale"].module()
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
        return

    # XXX WORK HARDER
    print(repr(locale_repo))
    raise NotImplementedError("not done!")
