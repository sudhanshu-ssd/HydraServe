from dependencies import (
    hash_password,
    verify_password,
    create_access_token,
    verify_access_token,
    hash_api,
    generate_api,
)


class TestPasswordHashing:

    def test_hash_and_verify_succeeds(self):
        raw = "MySecretPassword123!"
        hashed = hash_password(raw)
        assert hashed != raw
        assert verify_password(raw, hashed) is True

    def test_wrong_password_rejected(self):
        hashed = hash_password("CorrectPassword")
        assert verify_password("WrongPassword", hashed) is False

    def test_salted_hashes_differ(self):
        """Same password should produce different hashes (salted)."""
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2


class TestJWT:

    def test_create_and_verify_roundtrip(self):
        token = create_access_token(data={"sub": "42"})
        assert verify_access_token(token) == "42"

    def test_invalid_token_returns_none(self):
        assert verify_access_token("not.a.real.token") is None

    def test_tampered_token_returns_none(self):
        token = create_access_token(data={"sub": "42"})
        tampered = token[:-4] + "XXXX"
        assert verify_access_token(tampered) is None


class TestAPIKeyUtilities:

    def test_hash_api_is_deterministic(self):
        assert hash_api("my_key") == hash_api("my_key")

    def test_hash_api_differs_for_different_inputs(self):
        assert hash_api("key_a") != hash_api("key_b")

    def test_generate_api_has_prefix(self):
        key = generate_api(prefix="hs_")
        assert key.startswith("hs_")

    def test_generate_api_produces_unique_keys(self):
        keys = {generate_api() for _ in range(50)}
        assert len(keys) == 50, "Expected 50 unique API keys"
