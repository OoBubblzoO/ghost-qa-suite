"""Thin clients for Ghost's Content and Admin APIs.

Tests should read as intent ("create a post"), not HTTP plumbing.
These wrappers own base URLs, auth headers, and JSON envelopes;
assertions stay in the tests where they belong.
"""

from __future__ import annotations

from typing import Any

import httpx

from utils.ghost_auth import generate_admin_token


class ContentAPIClient:
    """Public, read-only Content API. Auth is a simple query-param key."""

    def __init__(self, base_url: str, content_api_key: str):
        self._key = content_api_key
        self.http = httpx.Client(
            base_url=f"{base_url}/ghost/api/content",
            timeout=10.0,
        )

    def get(self, path: str, **params: Any) -> httpx.Response:
        params["key"] = self._key
        return self.http.get(path, params=params)


class AdminAPIClient:
    """Authenticated Admin API. JWT is minted fresh per client instance."""

    def __init__(self, base_url: str, admin_api_key: str):
        self._api_key = admin_api_key
        self.http = httpx.Client(
            base_url=f"{base_url}/ghost/api/admin",
            timeout=10.0,
        )

    # -- internal ---------------------------------------------------------
    def _headers(self) -> dict[str, str]:
        # Fresh token per request: cheap to mint, and immune to the 5-minute
        # expiry biting a long-running suite.
        return {"Authorization": f"Ghost {generate_admin_token(self._api_key)}"}

    # -- generic verbs ----------------------------------------------------
    def get(self, path: str, **params: Any) -> httpx.Response:
        return self.http.get(path, params=params, headers=self._headers())

    def post(self, path: str, json: dict | None = None) -> httpx.Response:
        return self.http.post(path, json=json, headers=self._headers())

    def put(self, path: str, json: dict | None = None) -> httpx.Response:
        return self.http.put(path, json=json, headers=self._headers())

    def delete(self, path: str) -> httpx.Response:
        return self.http.delete(path, headers=self._headers())

    # -- domain helpers (used by fixtures/tests) ---------------------------
    def create_post(self, title: str, status: str = "draft", **fields: Any) -> httpx.Response:
        post = {"title": title, "status": status, **fields}
        return self.post("/posts/", json={"posts": [post]})

    def get_post(self, post_id: str) -> httpx.Response:
        return self.get(f"/posts/{post_id}/")

    def update_post(self, post_id: str, updated_at: str, **fields: Any) -> httpx.Response:
        # Ghost requires updated_at for optimistic-collision detection.
        post = {"updated_at": updated_at, **fields}
        return self.put(f"/posts/{post_id}/", json={"posts": [post]})

    def delete_post(self, post_id: str) -> httpx.Response:
        return self.delete(f"/posts/{post_id}/")
