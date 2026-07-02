"""Admin API authentication tests.

Auth is the highest-risk surface: a regression here is either a lockout
(availability) or a bypass (security). Both directions are covered.
"""

import time

import httpx
import jwt
import pytest

pytestmark = pytest.mark.critical


def _raw_admin_get(base_url: str, token: str | None) -> httpx.Response:
    headers = {"Authorization": f"Ghost {token}"} if token else {}
    return httpx.get(
        f"{base_url}/ghost/api/admin/posts/", headers=headers, timeout=10.0
    )


class TestAdminAuth:
    def test_valid_token_grants_access(self, admin_client):
        resp = admin_client.get("/posts/")
        assert resp.status_code == 200

    def test_missing_token_is_rejected(self, base_url):
        resp = _raw_admin_get(base_url, token=None)
        assert resp.status_code in (401, 403)

    def test_garbage_token_is_rejected(self, base_url):
        resp = _raw_admin_get(base_url, token="not.a.jwt")
        assert resp.status_code == 401

    @pytest.mark.regression
    def test_expired_token_is_rejected(self, base_url, admin_api_key):
        key_id, secret_hex = admin_api_key.split(":")
        past = int(time.time()) - 3600
        expired = jwt.encode(
            {"iat": past, "exp": past + 60, "aud": "/admin/"},
            bytes.fromhex(secret_hex),
            algorithm="HS256",
            headers={"kid": key_id},
        )
        resp = _raw_admin_get(base_url, token=expired)
        assert resp.status_code == 401

    @pytest.mark.regression
    def test_wrong_audience_is_rejected(self, base_url, admin_api_key):
        key_id, secret_hex = admin_api_key.split(":")
        now = int(time.time())
        wrong_aud = jwt.encode(
            {"iat": now, "exp": now + 300, "aud": "/content/"},
            bytes.fromhex(secret_hex),
            algorithm="HS256",
            headers={"kid": key_id},
        )
        resp = _raw_admin_get(base_url, token=wrong_aud)
        assert resp.status_code == 401

    @pytest.mark.regression
    def test_token_signed_with_wrong_secret_is_rejected(self, base_url, admin_api_key):
        key_id, _ = admin_api_key.split(":")
        now = int(time.time())
        forged = jwt.encode(
            {"iat": now, "exp": now + 300, "aud": "/admin/"},
            b"\x00" * 32,  # attacker doesn't know the real secret
            algorithm="HS256",
            headers={"kid": key_id},
        )
        resp = _raw_admin_get(base_url, token=forged)
        assert resp.status_code == 401
