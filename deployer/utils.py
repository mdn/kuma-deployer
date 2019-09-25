import click
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


def error(*msg):
    msg = " ".join([str(x) for x in msg])
    click.echo(click.style(msg, fg="red"))


def warning(*msg):
    msg = " ".join([str(x) for x in msg])
    click.echo(click.style(msg, fg="yellow"))


def info(*msg):
    msg = " ".join([str(x) for x in msg])
    click.echo(click.style(msg))


def success(*msg):
    msg = " ".join([str(x) for x in msg])
    click.echo(click.style(msg, fg="green"))


def requests_retry_session(
    retries=4, backoff_factor=0.4, status_forcelist=(500, 502, 504), session=None
):
    """Opinionated wrapper that creates a requests session with a
    HTTPAdapter that sets up a Retry policy that includes connection
    retries.

    If you do the more naive retry by simply setting a number. E.g.::

        adapter = HTTPAdapter(max_retries=3)

    then it will raise immediately on any connection errors.
    Retrying on connection errors guards better on unpredictable networks.
    From http://docs.python-requests.org/en/master/api/?highlight=retries#requests.adapters.HTTPAdapter
    it says: "By default, Requests does not retry failed connections."

    The backoff_factor is documented here:
    https://urllib3.readthedocs.io/en/latest/reference/urllib3.util.html#urllib3.util.retry.Retry
    A default of retries=3 and backoff_factor=0.3 means it will sleep like::

        [0.3, 0.6, 1.2]
    """  # noqa
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def _humanize_time(amount, units):
    """Chopped and changed from http://stackoverflow.com/a/6574789/205832"""
    intervals = (1, 60, 60 * 60, 60 * 60 * 24, 604800, 2419200, 29030400)
    names = (
        ("second", "seconds"),
        ("minute", "minutes"),
        ("hour", "hours"),
        ("day", "days"),
        ("week", "weeks"),
        ("month", "months"),
        ("year", "years"),
    )

    result = []
    unit = [x[1] for x in names].index(units)
    # Convert to seconds
    amount = amount * intervals[unit]
    for i in range(len(names) - 1, -1, -1):
        a = int(amount) // intervals[i]
        if a > 0:
            result.append((a, names[i][1 % a]))
            amount -= a * intervals[i]
    return result


def humanize_seconds(seconds):
    return "{} {}".format(*_humanize_time(seconds, "seconds")[0])
