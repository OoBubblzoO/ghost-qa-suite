"""Admin API — validation and negative tests.

Happy paths prove the feature works; these prove the API fails *safely*:
correct status codes, no 5xx on bad input, no resource created as a side
effect of a rejected request.
"""

import pytest

pytestmark = pytest.mark.regression


class TestPostsValidation:
    def test_create_post_without_title_is_handled(self, admin_client):
        resp = admin_client.post("/posts/", json={"posts": [{"status": "draft"}]})
        # Ghost historically accepts untitled posts as "(Untitled)"; either a
        # 201 with that default or a 422 rejection is acceptable. What is NOT
        # acceptable is a 5xx.
        assert resp.status_code < 500
        if resp.status_code == 201:
            post = resp.json()["posts"][0]
            admin_client.delete_post(post["id"])  # cleanup

    def test_malformed_body_is_rejected_not_crashed(self, admin_client):
        resp = admin_client.post("/posts/", json={"not_posts": []})
        assert 400 <= resp.status_code < 500

    def test_invalid_status_value_is_rejected(self, admin_client, unique_title):
        resp = admin_client.post(
            "/posts/",
            json={"posts": [{"title": unique_title, "status": "yolo"}]},
        )
        assert 400 <= resp.status_code < 500
        # And it must not have been created anyway:
        search = admin_client.get("/posts/", filter=f"title:'{unique_title}'")
        assert not search.json().get("posts"), "rejected post was still created"

    def test_oversized_title_boundary(self, admin_client):
        huge_title = "A" * 5000  # Ghost's posts.title column caps far below this
        resp = admin_client.create_post(title=huge_title)
        assert 400 <= resp.status_code < 500, (
            f"expected validation error for 5000-char title, got {resp.status_code}"
        )

    def test_get_nonexistent_post_returns_404(self, admin_client):
        resp = admin_client.get_post("5951f5fca366002ebd5dbef7")  # valid-shaped, absent
        assert resp.status_code == 404

    def test_update_with_stale_updated_at_is_rejected(self, admin_client, draft_post):
        stale = "2000-01-01T00:00:00.000Z"
        resp = admin_client.update_post(
            draft_post["id"], updated_at=stale, title="stale write"
        )
        # Ghost uses updated_at for collision detection; a stale timestamp
        # must be rejected (409/422 family), never silently applied.
        assert 400 <= resp.status_code < 500
