from dependencies import redis,database
from sqlalchemy import select
import models
from fastapi import HTTPException,status
import time
import uuid
from config import settings
import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

async def get_limits(model:str,project_id:int,db:AsyncSession):  
    results  = await db.execute(select(models.Models).where(models.Models.model_name == model))
    my_model = results.scalars().first()
    if not my_model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Model not Found")
    g_rpm = my_model.global_rpm
    g_rpd = my_model.global_rpd
    g_tpm = my_model.global_tpm
    g_tpd = my_model.global_tpd
    model_id = my_model.model_id
    
    results  = await db.execute(select(models.Project).where(models.Project.project_id == project_id))
    pro = results.scalars().first()
    if not pro:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Project not Found")
    rpm = pro.rpm
    rpd = pro.rpd
    tpm = pro.tpm
    tpd = pro.tpd

    return g_rpm,g_rpd,g_tpm,g_tpd,rpm,rpd,tpm,tpd,model_id

RATE_LIMIT_SCRIPT = """
-- KEYS[1] = project request set,  KEYS[2] = project token set
-- KEYS[3] = model request set,    KEYS[4] = model token set
-- ARGV[1]  = now
-- ARGV[2]  = minute_ago
-- ARGV[3]  = day_ago
-- ARGV[4]  = member_id (uuid)
-- ARGV[5]  = estimated_tokens
-- ARGV[6]  = project rpm limit
-- ARGV[7]  = project rpd limit
-- ARGV[8]  = project tpm limit
-- ARGV[9]  = project tpd limit
-- ARGV[10] = model rpm limit
-- ARGV[11] = model rpd limit
-- ARGV[12] = model tpm limit
-- ARGV[13] = model tpd limit

local now = tonumber(ARGV[1])
local minute_ago = tonumber(ARGV[2])
local day_ago = tonumber(ARGV[3])
local member_id = ARGV[4]
local est_tokens = tonumber(ARGV[5])

-- Cleanup: remove entries older than 1 day from all sets
for i = 1, 4 do
    redis.call('ZREMRANGEBYSCORE', KEYS[i], '-inf', day_ago)
end

-- Helper: sum token values from members in format "uuid:tokens"
local function sum_tokens(key, min_score)
    local entries = redis.call('ZRANGEBYSCORE', key, min_score, now)
    local total = 0
    for _, entry in ipairs(entries) do
        local tok = string.match(entry, ":(%d+)$")
        if tok then total = total + tonumber(tok) end
    end
    return total
end

-- Check request limits (RPM uses minute window, RPD uses full set after cleanup)
if redis.call('ZCOUNT', KEYS[1], minute_ago, now) >= tonumber(ARGV[6]) then return {0, "project_rpm"} end
if redis.call('ZCARD',  KEYS[1])                  >= tonumber(ARGV[7]) then return {0, "project_rpd"} end
if redis.call('ZCOUNT', KEYS[3], minute_ago, now) >= tonumber(ARGV[9]) then return {0, "model_rpm"}   end -- ARGV[10] was wrong in Claude's version
if redis.call('ZCARD',  KEYS[3])                  >= tonumber(ARGV[11]) then return {0, "model_rpd"}  end

-- Check token limits (including the estimated tokens we're about to add)
if sum_tokens(KEYS[2], minute_ago) + est_tokens > tonumber(ARGV[8])  then return {0, "project_tpm"} end
if sum_tokens(KEYS[2], day_ago)    + est_tokens > tonumber(ARGV[9])  then return {0, "project_tpd"} end
if sum_tokens(KEYS[4], minute_ago) + est_tokens > tonumber(ARGV[12]) then return {0, "model_tpm"}   end
if sum_tokens(KEYS[4], day_ago)    + est_tokens > tonumber(ARGV[13]) then return {0, "model_tpd"}   end

-- All checks passed — reserve slots
local token_member = member_id .. ":" .. ARGV[5]

redis.call('ZADD', KEYS[1], now, member_id)       -- project request
redis.call('ZADD', KEYS[2], now, token_member)     -- project tokens (estimated)
redis.call('ZADD', KEYS[3], now, member_id)        -- model request  
redis.call('ZADD', KEYS[4], now, token_member)     -- model tokens (estimated)

-- Set TTL on all keys (2 days — generous, cleanup handles precision)
for i = 1, 4 do
    redis.call('EXPIRE', KEYS[i], 172800)
end

return {1, "ok"}
"""



async def is_allowed(redis_client : aioredis.Redis , model: str, project_id: int, db: AsyncSession, estimated_tokens: int = 500):
    g_rpm, g_rpd, g_tpm, g_tpd, rpm, rpd, tpm, tpd, model_id = await get_limits(model, project_id, db)

    script = redis_client.register_script(RATE_LIMIT_SCRIPT)

    keys = [
        f"ratelimit:project:{project_id}:request",
        f"ratelimit:project:{project_id}:token",
        f"ratelimit:model:{model_id}:request",
        f"ratelimit:model:{model_id}:token",
    ]

    now = time.time()
    member_id = uuid.uuid4().hex

    result = await script(
        keys=keys,
        args=[
            now,                    # ARGV[1]
            now - 60,               # ARGV[2] minute_ago
            now - 86400,            # ARGV[3] day_ago
            member_id,              # ARGV[4]
            settings.estimated_tokens,       # ARGV[5]
            rpm, rpd, tpm, tpd,     # ARGV[6-9] project limits
            g_rpm, g_rpd, g_tpm, g_tpd  # ARGV[10-13] model limits
        ]
    )

    allowed = bool(result[0])
    reason = result[1]

    return allowed, reason, member_id, model_id # Return member_id for later correction


async def correct_tokens(redis_client: aioredis.Redis, project_id: int, model_id: int, member_id: str, estimated_tokens: int, actual_tokens: int):
    old_member = f"{member_id}:{estimated_tokens}"
    new_member = f"{member_id}:{actual_tokens}"

    for key in [
        f"ratelimit:project:{project_id}:token",
        f"ratelimit:model:{model_id}:token",
    ]:
        score = await redis_client.zscore(key, old_member)
        if score is not None:
            await redis_client.zrem(key, old_member)
            await redis_client.zadd(key, {new_member: score})