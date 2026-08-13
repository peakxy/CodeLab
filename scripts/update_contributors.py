#!/usr/bin/env python3
"""Refresh the CodeLab contributor leaderboard from GitHub commits."""

from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


REPOSITORY = os.environ.get("GITHUB_REPOSITORY", "peakxy/CodeLab")
API_ROOT = os.environ.get("GITHUB_API_URL", "https://api.github.com").rstrip("/")
OUTPUT = Path(__file__).resolve().parents[1] / "data" / "codelab_contributors.json"


def fetch_commits(page: int) -> list[dict]:
    query = urlencode({"per_page": 100, "page": page})
    request = Request(
        f"{API_ROOT}/repos/{REPOSITORY}/commits?{query}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "CodeLab-contributor-updater",
        },
    )
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")

    with urlopen(request, timeout=30) as response:
        payload = json.load(response)

    if not isinstance(payload, list):
        raise RuntimeError(f"GitHub returned an unexpected response: {payload!r}")
    return payload


def collect_contributors() -> list[dict]:
    contributors: dict[str, dict] = {}
    page = 1

    while True:
        commits = fetch_commits(page)
        if not commits:
            break

        for commit in commits:
            user = commit.get("author") or {}
            login = user.get("login")
            if not login:
                continue

            contributor = contributors.setdefault(
                login.lower(),
                {
                    "username": login,
                    "avatar_url": user.get("avatar_url", ""),
                    "profile_url": user.get("html_url", f"https://github.com/{login}"),
                    "contributions": 0,
                },
            )
            contributor["contributions"] += 1

        if len(commits) < 100:
            break
        page += 1

    return sorted(
        contributors.values(),
        key=lambda contributor: (
            -contributor["contributions"],
            contributor["username"].lower(),
        ),
    )


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(collect_contributors(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
