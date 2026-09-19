"""Small GitHub REST API client for monitoring a branch tip."""

from dataclasses import dataclass
from typing import Optional
from urllib.parse import quote

import requests


class GitHubError(Exception):
    """An expected GitHub API failure."""


@dataclass(frozen=True)
class Commit:
    sha: str
    author: str
    message: str


class GitHubMonitor:
    def __init__(self, owner: str, repo: str, branch: str, token: Optional[str]):
        self.owner = owner
        self.repo = repo
        self.branch = branch
        encoded_owner = quote(owner, safe="")
        encoded_repo = quote(repo, safe="")
        encoded_branch = quote(branch, safe="")
        self.url = f"https://api.github.com/repos/{encoded_owner}/{encoded_repo}/commits/{encoded_branch}"
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "push-producer-tag",
            }
        )
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"

    def latest_commit(self) -> Commit:
        try:
            response = self.session.get(self.url, timeout=15)
        except requests.RequestException as error:
            raise GitHubError(f"Network error while contacting GitHub: {error}") from error

        if response.status_code == 403 and response.headers.get("X-RateLimit-Remaining") == "0":
            reset_at = response.headers.get("X-RateLimit-Reset", "unknown")
            raise GitHubError(f"GitHub rate limit reached (resets at {reset_at})")
        if response.status_code == 404:
            raise GitHubError(
                f"Repository or branch not found: {self.owner}/{self.repo}@{self.branch}. "
                "Check the owner, repository, branch, and token permissions."
            )
        if response.status_code in (401, 403):
            raise GitHubError("GitHub rejected the token or it lacks permission for this repository")
        if not response.ok:
            raise GitHubError(f"GitHub API returned HTTP {response.status_code}: {response.text[:200]}")

        try:
            payload = response.json()
            commit_data = payload["commit"]
            author = commit_data["author"]["name"]
            message = commit_data["message"].splitlines()[0]
            return Commit(sha=payload["sha"], author=author, message=message)
        except (KeyError, TypeError, ValueError) as error:
            raise GitHubError("GitHub returned an unexpected commit response") from error
