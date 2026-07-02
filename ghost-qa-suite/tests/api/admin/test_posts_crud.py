"""Admin API — posts CRUD lifecycle.

Core business logic: create, read, update, publish, delete. Uses the
`draft_post` factory fixture, which owns cleanup, so every test here is
independently re-runnable.
"""

import pytest

pytestmark = pytest.mark.critical


class TestPostsCRUD:
    def test_create_draft_post(self, admin_client, unique_title):
        resp = admin_client.create_post(title=unique_title, status="draft")
        assert resp.status_code == 201
        post = resp.json()["posts"][0]
        try:
            assert post["title"] == unique_title
            assert post["status"] == "draft"
            assert post["slug"], "Ghost should auto-generate a slug"
        finally:
            admin_client.delete_post(post["id"])

    def test_read_post_by_id(self, admin_client, draft_post):
        resp = admin_client.get_post(draft_post["id"])
        assert resp.status_code == 200
        assert resp.json()["posts"][0]["id"] == draft_post["id"]

    def test_update_post_title(self, admin_client, draft_post):
        new_title = draft_post["title"] + " (edited)"
        resp = admin_client.update_post(
            draft_post["id"],
            updated_at=draft_post["updated_at"],
            title=new_title,
        )
        assert resp.status_code == 200
        assert resp.json()["posts"][0]["title"] == new_title

    def test_publish_flow_makes_post_public(self, admin_client, content_client, draft_post):
        # Draft -> published via Admin API...
        resp = admin_client.update_post(
            draft_post["id"],
            updated_at=draft_post["updated_at"],
            status="published",
        )
        assert resp.status_code == 200
        slug = resp.json()["posts"][0]["slug"]

        # ...must become visible on the public Content API.
        public = content_client.get(f"/posts/slug/{slug}/")
        assert public.status_code == 200, "published post not visible publicly"

    def test_delete_post(self, admin_client, unique_title):
        created = admin_client.create_post(title=unique_title).json()["posts"][0]
        resp = admin_client.delete_post(created["id"])
        assert resp.status_code == 204

        # Verify it's actually gone.
        assert admin_client.get_post(created["id"]).status_code == 404
