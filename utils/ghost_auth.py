"""Ghost Admin API authentication.

Ghost's Admin API authenticates with short-lived JWTs signed using an
Admin API key. The key (from Settings -> Integrations) has the form
"<id>:<secret>", where the secret is hex-encoded.

Token requirements (per Ghost Admin API docs):
  - algorithm: HS256
  - header must include `kid` = the key id
  - audience (`aud`) must be "/admin/"
  - max lifetime: 5 minutes

Design note: tests never touch this module directly — they use the
`admin_client` fixture, which injects a fresh token. Keeping auth in one
place means a Ghost auth change is a one-file fix.
"""

from __future__ import annotations

import time

import jwt


TOKEN_LIFETIME_SECONDS = 5 * 60  # Ghost rejects anything longer


def generate_admin_token(admin_api_key: str) -> str:
    """Build a signed JWT for the Ghost Admin API from an "id:secret" key."""
    try:
        key_id, secret_hex = admin_api_key.split(":")
    except ValueError as exc:
        raise ValueError(
            "GHOST_ADMIN_API_KEY must look like '<id>:<secret>' "
            "(copy it from Ghost Settings -> Integrations)."
        ) from exc

    now = int(time.time())
    payload = {
        "iat": now,
        "exp": now + TOKEN_LIFETIME_SECONDS,
        "aud": "/admin/",
    }
    return jwt.encode(
        payload,
        bytes.fromhex(secret_hex),
        algorithm="HS256",
        headers={"kid": key_id},
    )
