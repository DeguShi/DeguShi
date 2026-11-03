"""Fetch everything the card shows from the GitHub GraphQL API."""

from __future__ import annotations

import json
import urllib.request
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
    repositories(ownerAffiliations: OWNER, isFork: false, first: 100) {
      totalCount
      nodes { pushedAt primaryLanguage { name } }
    }
  }
}
"""

# Notebooks are how the Python research gets written; count them as Python.
LANG_ALIASES = {"Jupyter Notebook": "Python"}


@dataclass(frozen=True)
class Day:
    day: date
    count: int


@dataclass(frozen=True)
class Stats:
    total: int
    commits: int
    pull_requests: int
    repos: int  # active in the last year
    weeks: list[list[Day]]
    languages: list[tuple[str, int]]


def graphql(query: str, variables: dict[str, str], token: str) -> dict:
    """POST one GraphQL query and return its `data` field."""
    body = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.load(resp)
    if "errors" in payload:
        raise RuntimeError(f"GraphQL error: {payload['errors']}")
    return payload["data"]


def active_repos(nodes: list[dict], days: int = 365) -> list[dict]:
    """Repos with a primary language that were pushed to within the last `days` days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return [n for n in nodes if n["primaryLanguage"]
            and datetime.fromisoformat(n["pushedAt"].replace("Z", "+00:00")) >= cutoff]


def fetch_stats(login: str, token: str) -> Stats:
    """Contribution calendar, headline counts and repo languages for one user."""
    user = graphql(QUERY, {"login": login}, token)["user"]
    cc = user["contributionsCollection"]
    cal = cc["contributionCalendar"]
    weeks = [[Day(date.fromisoformat(d["date"]), d["contributionCount"]) for d in w["contributionDays"]]
             for w in cal["weeks"]]
    active = active_repos(user["repositories"]["nodes"])
    langs = Counter(LANG_ALIASES.get(n["primaryLanguage"]["name"], n["primaryLanguage"]["name"]) for n in active)
    return Stats(
        total=cal["totalContributions"],
        commits=cc["totalCommitContributions"],
        pull_requests=cc["totalPullRequestContributions"],
        repos=len(active),
        weeks=weeks,
        languages=langs.most_common(),
    )
