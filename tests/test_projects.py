from httpx import AsyncClient


class TestProjectCRUD:

    async def test_create_project(self, client: AsyncClient, auth_headers):
        resp = await client.post(
            "/projects",
            json={"name": "My Project", "description": "Test description"},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["name"] == "My Project"
        assert "project_id" in body

    async def test_list_projects_includes_created(
        self, client: AsyncClient, auth_headers, test_project
    ):
        resp = await client.get("/projects", headers=auth_headers)
        assert resp.status_code == 200
        projects = resp.json()
        assert len(projects) >= 1
        assert any(p["name"] == test_project["name"] for p in projects)

    async def test_update_project_name(
        self, client: AsyncClient, auth_headers, test_project
    ):
        pro_id = test_project["project_id"]
        resp = await client.patch(
            f"/projects/{pro_id}",
            json={"name": "Updated Name", "description": "Updated desc"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Name"

    async def test_delete_project(
        self, client: AsyncClient, auth_headers, test_project
    ):
        pro_id = test_project["project_id"]
        resp = await client.delete(f"/projects/{pro_id}", headers=auth_headers)
        assert resp.status_code == 200

    async def test_update_other_users_project_forbidden(
        self, client: AsyncClient, test_project
    ):
        await client.post(
            "/users/register",
            json={
                "username": "attacker",
                "email": "attacker@evil.com",
                "password": "HackPass1!",
            },
        )
        login_resp = await client.post(
            "/token",
            data={"username": "attacker@evil.com", "password": "HackPass1!"},
        )
        attacker_headers = {
            "Authorization": f"Bearer {login_resp.json()['access_token']}"
        }

        pro_id = test_project["project_id"]
        resp = await client.patch(
            f"/projects/{pro_id}",
            json={"name": "Hacked", "description": "Hacked desc"},
            headers=attacker_headers,
        )
        assert resp.status_code != 200, "Cross-user project update must be rejected"
        assert resp.status_code in (403, 401, 500)


class TestAPIKeys:

    async def test_create_api_key_returns_prefixed_key(
        self, client: AsyncClient, auth_headers, test_project
    ):
        pro_id = test_project["project_id"]
        resp = await client.post(
            f"/projects/{pro_id}/keys", 
            headers=auth_headers,
            json={"name": "test_key"}
        )
        assert resp.status_code == 201
        assert resp.json()["api_key"].startswith("hs_")

    async def test_create_api_key_unauthorized_project(
        self, client: AsyncClient, auth_headers
    ):
        resp = await client.post(
            "/projects/99999/keys", 
            headers=auth_headers,
            json={"name": "test_key"}
        )
        assert resp.status_code != 201, "Key for non-existent project must fail"
        assert resp.status_code in (401, 403, 404, 500)
