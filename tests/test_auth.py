"""Tests for authentication and user registration flows."""
from httpx import AsyncClient


class TestRegistration:
    """User signup — happy path and duplicate guards."""

    async def test_register_success(self, client: AsyncClient):
        resp = await client.post(
            "/users/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "Secure123!",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["username"] == "newuser"

    async def test_register_duplicate_username_rejected(
        self, client: AsyncClient, registered_user
    ):
        """Duplicate username must not succeed — the app should return
        400 (explicit check) or let the DB UNIQUE constraint reject it."""
        resp = await client.post(
            "/users/register",
            json={
                "username": registered_user["username"],  # duplicate
                "email": "different@example.com",
                "password": "Secure123!",
            },
        )
        assert resp.status_code != 201, "Duplicate username must not be accepted"
        assert resp.status_code in (400, 409, 500)

    async def test_register_duplicate_email_rejected(
        self, client: AsyncClient, registered_user
    ):
        """Duplicate email must not succeed."""
        resp = await client.post(
            "/users/register",
            json={
                "username": "differentuser",
                "email": registered_user["email"],  # duplicate
                "password": "Secure123!",
            },
        )
        assert resp.status_code != 201, "Duplicate email must not be accepted"
        assert resp.status_code in (400, 409, 500)


class TestLogin:
    """Token endpoint — correct & incorrect credentials."""

    async def test_login_success(self, client: AsyncClient, registered_user):
        resp = await client.post(
            "/token",
            data={
                "username": registered_user["email"],
                "password": registered_user["password"],
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "Bearer"

    async def test_login_wrong_password(self, client: AsyncClient, registered_user):
        resp = await client.post(
            "/token",
            data={
                "username": registered_user["email"],
                "password": "WrongPassword!",
            },
        )
        assert resp.status_code == 401

    async def test_login_nonexistent_email(self, client: AsyncClient):
        resp = await client.post(
            "/token",
            data={"username": "nobody@example.com", "password": "anything"},
        )
        assert resp.status_code == 401


class TestTokenValidation:
    """Protected endpoints reject missing / invalid tokens."""

    async def test_no_token_returns_401(self, client: AsyncClient):
        resp = await client.get("/projects")
        assert resp.status_code == 401

    async def test_invalid_token_returns_401(self, client: AsyncClient):
        resp = await client.get(
            "/projects",
            headers={"Authorization": "Bearer totally.invalid.token"},
        )
        assert resp.status_code == 401
