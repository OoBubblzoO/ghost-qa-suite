"""Content API smoke tests.

Fast, read-only, no side effects. These gate every commit: if the public
Content API is down or malformed, nothing else matters.
"""

import pytest

pytestmark = pytest.mark.smoke


class TestContentAPISmoke:
    def test_posts_endpoint_returns_200_and_envelope(self, content_client):
        resp = content_client.get("/posts/")
        assert resp.status_code == 200
        body = resp.json()
        assert "posts" in body, "response missing 'posts' envelope"
        assert "meta" in body, "response missing pagination 'meta'"

    def test_posts_have_required_public_fields(self, content_client):
        resp = content_client.get("/posts/", limit=1)
        posts = resp.json()["posts"]
        assert posts, "expected at least the default Ghost welcome post"
        post = posts[0]
        for field in ("id", "title", "slug", "html", "url"):
            assert field in post, f"post missing public field '{field}'"

    def test_pagination_limit_is_respected(self, content_client):
        resp = content_client.get("/posts/", limit=2)
        body = resp.json()
        assert len(body["posts"]) <= 2
        assert body["meta"]["pagination"]["limit"] == 2

    def test_tags_endpoint_returns_200(self, content_client):
        resp = content_client.get("/tags/")
        assert resp.status_code == 200
        assert "tags" in resp.json()

    def test_invalid_content_key_is_rejected(self, base_url):
        # Bypass the fixture client on purpose: we're testing the key itself.
        import httpx

        resp = httpx.get(
            f"{base_url}/ghost/api/content/posts/",
            params={"key": "0" * 26},
            timeout=10.0,
        )
        assert resp.status_code == 401
