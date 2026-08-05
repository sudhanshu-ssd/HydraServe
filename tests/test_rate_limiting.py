from unittest.mock import AsyncMock
from services.rate_service import correct_tokens
from config import settings


class TestCorrectTokens:

    async def test_replaces_estimated_with_actual(self):
        mock_redis = AsyncMock()
        mock_redis.zscore.return_value = 1719849600.0  

        await correct_tokens(
            redis_client=mock_redis,
            project_id=1,
            model_id=1,
            member_id="abc123",
            actual_tokens=200,
        )

        assert mock_redis.zrem.await_count == 2
        assert mock_redis.zadd.await_count == 2

        expected_old = f"abc123:{settings.estimated_tokens}"
        expected_new = "abc123:200"

        first_zrem = mock_redis.zrem.call_args_list[0]
        assert first_zrem[0][1] == expected_old  

        first_zadd = mock_redis.zadd.call_args_list[0]
        assert expected_new in first_zadd[0][1]  

    async def test_skips_correction_if_member_not_found(self):
        mock_redis = AsyncMock()
        mock_redis.zscore.return_value = None  # member not in set

        await correct_tokens(
            redis_client=mock_redis,
            project_id=1,
            model_id=1,
            member_id="nonexistent",  #unexistence would have been better lol
            actual_tokens=200,
        )

        mock_redis.zrem.assert_not_awaited()
        mock_redis.zadd.assert_not_awaited()
