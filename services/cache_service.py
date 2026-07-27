import hashlib
import json
import redis.asyncio as aioredis


def hash_user_req(prompt:str,model:str,system_prompt:str,max_tokens:int):
    data = json.dumps(
        {
            'user_prompt':prompt,
            "model":model,
            "system_prompt":system_prompt,
            "max_tokens":max_tokens,
        },sort_keys = True              #no idea what difference sort keys make here lol
    )
    return f"cache:{hashlib.sha256(data.encode()).hexdigest()}"

async def get_cached_response(redis_client : aioredis.Redis , key):
    data = await redis_client.get(key)
    if data:
        return json.loads(data)
        
async def set_cached_response(redis_client : aioredis.Redis , key ,model_id,pro_id,prompt_token,response_token,total_token,text):

            dict_data = {
                "model_id":model_id,
                "project_id":pro_id,
                "prompt_token" : prompt_token,
                "response_token" : response_token,
                "total_token" : total_token,
                "text":text
            }
            await redis_client.set(key, json.dumps(dict_data), ex=172800)




        