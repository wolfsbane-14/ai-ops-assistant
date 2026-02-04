from __future__ import annotations

import os
from typing import Any, Dict, List

import httpx


class GitHubTool:
    """GitHub API tool for repository search and details."""

    def __init__(self) -> None:
        self._token = os.getenv("GITHUB_TOKEN")
        self._base_url = "https://api.github.com"

    def _headers(self) -> Dict[str, str]:
        headers = {"Accept": "application/vnd.github+json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    def search_repositories(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        query = payload.get("query")
        if not query:
            raise ValueError("query is required for github_search")
        per_page = int(payload.get("per_page", 5))
        params = {"q": query, "per_page": per_page}
        with httpx.Client(timeout=10) as client:
            response = client.get(
                f"{self._base_url}/search/repositories",
                headers=self._headers(),
                params=params,
            )
            response.raise_for_status()
            data = response.json()
        items = [
            {
                "name": item["full_name"],
                "url": item["html_url"],
                "stars": item["stargazers_count"],
                "description": item["description"],
            }
            for item in data.get("items", [])
        ]
        return {"count": len(items), "items": items}

    def repo_details(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        full_name = payload.get("full_name")
        if not full_name:
            raise ValueError("full_name is required for github_repo_details")
        with httpx.Client(timeout=10) as client:
            response = client.get(
                f"{self._base_url}/repos/{full_name}",
                headers=self._headers(),
            )
            response.raise_for_status()
            data = response.json()
        return {
            "name": data.get("full_name"),
            "url": data.get("html_url"),
            "stars": data.get("stargazers_count"),
            "forks": data.get("forks_count"),
            "open_issues": data.get("open_issues_count"),
            "language": data.get("language"),
            "description": data.get("description"),
        }
