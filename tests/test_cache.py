"""
Unit tests for the Redis cache service.

All Redis interactions are mocked — no running Redis instance required.
"""
import json
from unittest.mock import AsyncMock

from services.cache_service import (
    hash_user_req,
    get_cached_response,
    set_cached_response,
)


class TestHashUserReq:
    """Cache-key generation from request parameters."""

    def test_same_inputs_produce_same_hash(self):
        h1 = hash_user_req("hello", "gpt-4", "be helpful", 512)
        h2 = hash_user_req("hello", "gpt-4", "be helpful", 512)
        assert h1 == h2

    def test_different_prompt_produces_different_hash(self):
        h1 = hash_user_req("hello", "gpt-4", "be helpful", 512)
        h2 = hash_user_req("goodbye", "gpt-4", "be helpful", 512)
        assert h1 != h2

    def test_different_model_produces_different_hash(self):
        h1 = hash_user_req("hello", "gpt-4", "be helpful", 512)
        h2 = hash_user_req("hello", "llama-3", "be helpful", 512)
        assert h1 != h2

    def test_hash_has_cache_prefix(self):
        h = hash_user_req("prompt", "model", "sys", 50)
        assert h.startswith("cache:")


class TestCacheGetSet:
    """Reading and writing cached LLM responses."""

    async def test_cache_hit_returns_stored_data(self):
        mock_redis = AsyncMock()
        cached_data = {
            "text": "cached answer",
            "model_id": 1,
            "project_id": 2,
            "prompt_token": 10,
            "response_token": 20,
            "total_token": 30,
        }
        mock_redis.get.return_value = json.dumps(cached_data)

        result = await get_cached_response(mock_redis, "cache:abc123")

        assert result is not None
        assert result["text"] == "cached answer"
        assert result["total_token"] == 30
        mock_redis.get.assert_awaited_once_with("cache:abc123")

    async def test_cache_miss_returns_none(self):
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None

        result = await get_cached_response(mock_redis, "cache:missing")

        assert result is None

    async def test_set_cached_response_stores_json(self):
        mock_redis = AsyncMock()

        await set_cached_response(
            redis_client=mock_redis,
            key="cache:xyz",
            model_id=1,
            pro_id=2,
            prompt_token=15,
            response_token=25,
            total_token=40,
            text="generated answer",
        )

        mock_redis.set.assert_awaited_once()
        args = mock_redis.set.call_args
        stored = json.loads(args[0][1])
        assert stored["text"] == "generated answer"
        assert stored["total_token"] == 40
        assert stored["model_id"] == 1
        # TTL should be set (ex=172800 = 2 days)
        assert args[1]["ex"] == 172800
