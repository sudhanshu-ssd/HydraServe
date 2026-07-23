import redis.asyncio as aioredis


# purely doing this for acoiding circular imports 
redis_client: aioredis.Redis | None = None    