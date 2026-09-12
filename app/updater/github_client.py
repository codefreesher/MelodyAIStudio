"""Public GitHub release metadata transport."""

import re

import httpx


class GitHubClient:
    def latest(self, owner: str, repository: str) -> dict:
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", owner) or not re.fullmatch(r"[A-Za-z0-9_.-]+", repository):
            raise ValueError("Chưa cấu hình GitHub owner/repository hợp lệ.")
        with httpx.Client(timeout=15) as client:
            response = client.get(
                f"https://api.github.com/repos/{owner}/{repository}/releases/latest",
                headers={"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2026-03-10"},
            )
            response.raise_for_status()
            return response.json()
