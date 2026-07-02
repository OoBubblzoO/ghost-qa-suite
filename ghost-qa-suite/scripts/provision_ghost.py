"""Provision a fresh Ghost instance for CI.

A brand-new Ghost container has no owner account and no API keys. This
script automates what a human does once in the browser:

  1. POST /ghost/api/admin/authentication/setup  -> create the owner account
  2. Log in with session auth
  3. Create a custom integration -> yields Content + Admin API keys

It prints KEY=VALUE lines so CI can append them to $GITHUB_ENV. For local
use, redirect the output into your .env file:

    python scripts/provision_ghost.py > .env
"""

from __future__ import annotations

import os
import sys
import time

import httpx

BASE_URL = os.environ.get("GHOST_BASE_URL", "http://localhost:2368")
OWNER_EMAIL = os.environ.get("GHOST_ADMIN_EMAIL", "qa-owner@example.com")
OWNER_PASSWORD = os.environ.get("GHOST_ADMIN_PASSWORD", "Str0ng-QA-P@ssw0rd!")
OWNER_NAME = "QA Suite Owner"


def wait_for_ghost(client: httpx.Client, timeout: int = 120) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if client.get(f"{BASE_URL}/ghost/api/admin/site/").status_code < 500:
                return
        except httpx.TransportError:
            pass
        time.sleep(2)
    sys.exit("Ghost never became reachable")


def main() -> None:
    with httpx.Client(timeout=30.0) as client:
        wait_for_ghost(client)

        # 1. One-time owner setup (409 means it already exists — fine locally).
        setup = client.post(
            f"{BASE_URL}/ghost/api/admin/authentication/setup/",
            json={
                "setup": [
                    {
                        "name": OWNER_NAME,
                        "email": OWNER_EMAIL,
                        "password": OWNER_PASSWORD,
                        "blogTitle": "QA Target",
                    }
                ]
            },
        )
        if setup.status_code not in (200, 201) and "already" not in setup.text.lower():
            sys.exit(f"Setup failed ({setup.status_code}): {setup.text}")

        # 2. Session login.
        session = client.post(
            f"{BASE_URL}/ghost/api/admin/session/",
            json={"username": OWNER_EMAIL, "password": OWNER_PASSWORD},
        )
        if session.status_code not in (200, 201):
            sys.exit(f"Login failed ({session.status_code}): {session.text}")

        # 3. Create the integration that yields both API keys.
        integration = client.post(
            f"{BASE_URL}/ghost/api/admin/integrations/?include=api_keys",
            json={"integrations": [{"name": f"qa-suite-{int(time.time())}"}]},
        )
        if integration.status_code != 201:
            sys.exit(f"Integration failed ({integration.status_code}): {integration.text}")

        keys = integration.json()["integrations"][0]["api_keys"]
        content_key = next(k["secret"] for k in keys if k["type"] == "content")
        admin_key = next(
            f"{k['id']}:{k['secret']}" for k in keys if k["type"] == "admin"
        )

    print(f"GHOST_BASE_URL={BASE_URL}")
    print(f"GHOST_CONTENT_API_KEY={content_key}")
    print(f"GHOST_ADMIN_API_KEY={admin_key}")
    print(f"GHOST_ADMIN_EMAIL={OWNER_EMAIL}")
    print(f"GHOST_ADMIN_PASSWORD={OWNER_PASSWORD}")


if __name__ == "__main__":
    main()
