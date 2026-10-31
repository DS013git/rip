"""Fetch factual repository metadata from GitHub, with a small local cache."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests
from dotenv import dotenv_values


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_PATH = PROJECT_ROOT / "data" / "sample_graveyard.json"
CACHE_DIR = PROJECT_ROOT / ".cache"
CACHE_TTL_SECONDS = 15 * 60
REQUEST_TIMEOUT_SECONDS = 10
GITHUB_API = "https://api.github.com"


def classify_status(days_since_last_push: int) -> str:
    """Return a graveyard status using the project's 30/90 day thresholds."""
    if days_since_last_push > 90:
        return "dead"
    if days_since_last_push > 30:
        return "dying"
    return "alive"


def load_sample_data(limit: int | None = None) -> list[dict[str, Any]]:
    """Load the bundled offline demo repos without making network requests."""
    with SAMPLE_PATH.open(encoding="utf-8") as sample_file:
        repos = json.load(sample_file)
    return repos[:limit] if limit is not None else repos


def _cache_path(url: str, params: dict[str, Any] | None, authenticated: bool) -> Path:
    cache_key = json.dumps(
        {"url": url, "params": params or {}, "authenticated": authenticated},
        sort_keys=True,
    )
    digest = hashlib.sha256(cache_key.encode("utf-8")).hexdigest()
    return CACHE_DIR / f"{digest}.json"


def _cached_get(url: str, *, params: dict[str, Any] | None, token: str | None) -> Any:
    """Read a fresh cached response, otherwise make and cache one GET request."""
    cache_file = _cache_path(url, params, authenticated=bool(token))
    try:
        cached = json.loads(cache_file.read_text(encoding="utf-8"))
        age = datetime.now(timezone.utc).timestamp() - cached["saved_at"]
        if age < CACHE_TTL_SECONDS:
            return cached["data"]
    except (OSError, ValueError, KeyError, TypeError):
        pass

    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    if response.status_code in (403, 429):
        raise RuntimeError(
            "GitHub API rate limit or access restriction reached. Add a token to "
            "GITHUB_TOKEN in your .env file, then try again."
        )
    response.raise_for_status()
    data = response.json()
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(
            json.dumps(
                {"saved_at": datetime.now(timezone.utc).timestamp(), "data": data},
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
    except OSError:
        # Cache failures should not prevent a useful GitHub response from working.
        pass
    return data


def _days_since(timestamp: str) -> int:
    pushed_at = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    return max(0, (datetime.now(timezone.utc) - pushed_at).days)


def _last_commit_message(owner: str, repo_name: str, token: str | None) -> str:
    url = f"{GITHUB_API}/repos/{quote(owner, safe='')}/{quote(repo_name, safe='')}/commits"
    try:
        commits = _cached_get(url, params={"per_page": 1}, token=token)
        if not commits:
            return ""
        message = commits[0].get("commit", {}).get("message", "")
        return message.splitlines()[0] if message else ""
    except RuntimeError:
        # A rate-limit response must be surfaced so the user can add a token.
        raise
    except (requests.RequestException, ValueError, KeyError, IndexError, TypeError):
        return ""


def fetch_repositories(
    username: str,
    limit: int = 30,
) -> list[dict[str, Any]]:
    """Return up to ``limit`` non-fork, non-empty repositories, oldest first."""
    if limit < 1:
        return []
    # GitHub credentials are deliberately read only from the local .env file.
    token = dotenv_values(PROJECT_ROOT / ".env").get("GITHUB_TOKEN") or None
    owner = quote(username, safe="")
    repos: list[dict[str, Any]] = []

    # Walk pages so users with more than 100 repositories can still be sorted
    # correctly before the requested limit is applied.
    page = 1
    while True:
        page_data = _cached_get(
            f"{GITHUB_API}/users/{owner}/repos",
            params={"per_page": 100, "type": "owner", "sort": "pushed", "page": page},
            token=token,
        )
        if not page_data:
            break
        for repo in page_data:
            if repo.get("fork") or repo.get("size", 0) == 0:
                continue
            days = _days_since(repo["pushed_at"])
            repos.append(
                {
                    "name": repo["name"],
                    "description": repo.get("description") or "",
                    "language": repo.get("language"),
                    "stars": repo.get("stargazers_count", 0),
                    "open_issues": repo.get("open_issues_count", 0),
                    "days_since_last_push": days,
                    "status": classify_status(days),
                    "last_commit_message": "",
                }
            )
        if len(page_data) < 100:
            break
        page += 1

    repos.sort(key=lambda item: item["days_since_last_push"], reverse=True)
    selected = repos[:limit]
    for repo in selected:
        repo["last_commit_message"] = _last_commit_message(username, repo["name"], token)
    return selected
