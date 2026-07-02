"""Shared fixtures.

Fixture philosophy:
  - Session-scoped clients: auth/config resolved once, reused everywhere.
  - Factory fixtures own their test data lifecycle: anything they create,
    they delete in teardown. The suite is safe to re-run and to run in
    parallel because every resource name is unique.
"""

from __future__ import annotations

import os
import uuid

import pytest
from dotenv import load_dotenv

from utils.api_client import AdminAPIClient, ContentAPIClient

load_dotenv()


# --- configuration -------------------------------------------------------

@pytest.fixture(scope="session")
def base_url() -> str:
    return os.environ.get("GHOST_BASE_URL", "http://localhost:2368")


@pytest.fixture(scope="session")
def content_api_key() -> str:
    key = os.environ.get("GHOST_CONTENT_API_KEY")
    if not key:
        pytest.skip("GHOST_CONTENT_API_KEY not set (see .env.example)")
    return key


@pytest.fixture(scope="session")
def admin_api_key() -> str:
    key = os.environ.get("GHOST_ADMIN_API_KEY")
    if not key:
        pytest.skip("GHOST_ADMIN_API_KEY not set (see .env.example)")
    return key


# --- API clients ---------------------------------------------------------

@pytest.fixture(scope="session")
def content_client(base_url, content_api_key) -> ContentAPIClient:
    return ContentAPIClient(base_url, content_api_key)


@pytest.fixture(scope="session")
def admin_client(base_url, admin_api_key) -> AdminAPIClient:
    return AdminAPIClient(base_url, admin_api_key)


# --- test data factories --------------------------------------------------

@pytest.fixture
def unique_title() -> str:
    """Unique per test so runs never collide with each other or with leftovers."""
    return f"qa-suite {uuid.uuid4().hex[:12]}"


@pytest.fixture
def draft_post(admin_client, unique_title) -> dict:
    """Create a draft post; guarantee cleanup even if the test fails."""
    resp = admin_client.create_post(title=unique_title, status="draft")
    assert resp.status_code == 201, f"fixture setup failed: {resp.text}"
    post = resp.json()["posts"][0]
    yield post
    admin_client.delete_post(post["id"])  # idempotent enough: 204 or 404
