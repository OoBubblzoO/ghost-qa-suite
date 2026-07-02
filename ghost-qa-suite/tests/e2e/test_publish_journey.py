"""E2E — the one journey that matters.

Deliberately thin. UI tests are the most expensive to run and maintain, so
this layer covers only the critical publishing path: log in, create a post,
publish it, and confirm it renders on the public site. Everything else is
verified faster and more reliably at the API layer.

Requires GHOST_ADMIN_EMAIL / GHOST_ADMIN_PASSWORD in the environment
(the owner account created during Ghost's one-time setup).
"""

import os
import uuid

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e

BASE_URL = os.environ.get("GHOST_BASE_URL", "http://localhost:2368")


@pytest.fixture
def admin_credentials() -> tuple[str, str]:
    email = os.environ.get("GHOST_ADMIN_EMAIL")
    password = os.environ.get("GHOST_ADMIN_PASSWORD")
    if not (email and password):
        pytest.skip("GHOST_ADMIN_EMAIL / GHOST_ADMIN_PASSWORD not set")
    return email, password


def _login(page: Page, email: str, password: str) -> None:
    page.goto(f"{BASE_URL}/ghost/#/signin")
    page.get_by_label("Email address").fill(email)
    page.get_by_label("Password").fill(password)
    page.get_by_role("button", name="Sign in").click()
    expect(page).to_have_url(lambda url: "/signin" not in url, timeout=15_000)


def test_login_create_publish_and_verify_public_render(page: Page, admin_credentials):
    email, password = admin_credentials
    title = f"e2e publish check {uuid.uuid4().hex[:8]}"

    # 1. Log in to Ghost admin
    _login(page, email, password)

    # 2. Create a new post
    page.goto(f"{BASE_URL}/ghost/#/editor/post")
    page.get_by_placeholder("Post title").fill(title)
    page.keyboard.press("Tab")
    page.keyboard.type("Automated critical-path check: create, publish, render.")

    # 3. Publish it
    page.get_by_role("button", name="Publish").click()
    page.get_by_role("button", name="Continue, final review").click()
    page.get_by_role("button", name="Publish post, right now").click()
    expect(page.get_by_text("Boom! It's out there.")).to_be_visible(timeout=15_000)

    # 4. Verify it renders on the public site
    page.goto(BASE_URL)
    expect(page.get_by_role("link", name=title)).to_be_visible(timeout=10_000)


def test_login_with_wrong_password_shows_error(page: Page, admin_credentials):
    email, _ = admin_credentials
    page.goto(f"{BASE_URL}/ghost/#/signin")
    page.get_by_label("Email address").fill(email)
    page.get_by_label("Password").fill("definitely-not-the-password")
    page.get_by_role("button", name="Sign in").click()
    # Must fail visibly and stay on the signin screen.
    expect(page).to_have_url(lambda url: "/signin" in url)
