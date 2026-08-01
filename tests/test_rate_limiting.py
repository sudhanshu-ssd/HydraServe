"""
Unit tests for rate-limiting token correction.

Tests the correct_tokens function that adjusts estimated token counts
in Redis sorted sets after the actual LLM response arrives.
"""
from unittest.mock import AsyncMock
from services.rate_service import correct_tokens
from config import settings


class TestCorrectTokens:
    """Post-hoc token correction in Redis sorted sets."""

    async def test_replaces_estimated_with_actual(self):
        """When the member exists, old entry is removed and new one added."""
        mock_redis = AsyncMock()
        mock_redis.zscore.return_value = 1719849600.0  # a valid timestamp

        await correct_tokens(
            redis_client=mock_redis,
            project_id=1,
            model_id=1,
            member_id="abc123",
            actual_tokens=200,
        )

        # Should call zrem + zadd for BOTH project-token and model-token keys
        assert mock_redis.zrem.await_count == 2
        assert mock_redis.zadd.await_count == 2

        # Verify the old member used the estimated_tokens from settings
        expected_old = f"abc123:{settings.estimated_tokens}"
        expected_new = "abc123:200"

        first_zrem = mock_redis.zrem.call_args_list[0]
        assert first_zrem[0][1] == expected_old  # removed old member

        first_zadd = mock_redis.zadd.call_args_list[0]
        assert expected_new in first_zadd[0][1]  # added new member

    async def test_skips_correction_if_member_not_found(self):
        """If the member doesn't exist in the sorted set, nothing is modified."""
        mock_redis = AsyncMock()
        mock_redis.zscore.return_value = None  # member not in set

        await correct_tokens(
            redis_client=mock_redis,
            project_id=1,
            model_id=1,
            member_id="nonexistent",
            actual_tokens=200,
        )

        mock_redis.zrem.assert_not_awaited()
        mock_redis.zadd.assert_not_awaited()
