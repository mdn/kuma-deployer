import shlex
import subprocess
import sys
import time

import git

from .utils import info, success, warning


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
    # process = subprocess.Popen(
    #     shlex.split(cmd), stdout=subprocess.PIPE, cwd=repo_location
    # )
    # import sys

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

    locale_submodule = repo.submodules["locale"]
    # XXX WORK HARDER
    print(repr(locale_submodule))
    raise NotImplementedError("not done!")
