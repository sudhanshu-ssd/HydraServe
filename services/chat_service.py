import  redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession
from schema import UserPrompt,UserPromptResponse
import models
import time
from services.cache_service import cache_user_req,get_cached_response,set_cached_response
from services.rate_service import is_allowed,correct_tokens
from fastapi import HTTPException,status
from services.providers import Provider_dict,Provider_Fallback
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

async def write_log(db:AsyncSession,model_id,project_id,user_id,prompt_token,response_token,total_token,latency,stat):
    new_log = models.Logs(
         model_id = model_id,
         project_id = project_id,
         user_id = user_id,
         prompt_token = prompt_token,
         response_token =response_token,
         total_token = total_token,
         latency = latency,
         status = stat
         )
    try:
        db.add(new_log)
        await db.commit()
    except Exception:
        await db.rollback()

async def handle_chat_request(details : UserPrompt, current_api , db : AsyncSession, redis_client:aioredis.Redis) -> str:

    start = time.time()
    pro_id = current_api.project_id

    key = cache_user_req(prompt=details.prompt,model=details.model,system_prompt=details.system_prompt,max_tokens=details.max_tokens)
    if details.model_temp < 1:
        response = await get_cached_response(redis_client=redis_client,key=key)
        if response:
            now=time.time() - start
            await write_log(db,response['model_id'],response['project_id'],current_api.user_id,response['prompt_token'],response['response_token'],response['total_token'],latency=now ,stat="CACHED")
            return response['text']
    
    prompt_token = response_token = total_token = None
    sta = 'FAILED'
    
    allowed,reason,member_id,model_id,provider_name = await is_allowed(redis_client=redis_client,model=details.model,project_id=pro_id,db=db)
    if not allowed:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS,detail=f"{reason} limit reached !!!!")
    
    try:
        text,total_token,prompt_token,response_token = await generate_retry_fallback(provider_name=provider_name,details=details)
        sta = 'SUCCESS'
        await correct_tokens(redis_client,pro_id,model_id=model_id,member_id=member_id,actual_tokens=total_token)


    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Provider Down") from e
    
    finally:
        now=time.time() - start
        await write_log(db,model_id,pro_id,current_api.user_id,prompt_token,response_token,total_token,latency = now,stat=sta)

    return text

    


async def generate_retry_fallback(provider_name,details : UserPrompt):
    # chatbot = Provider_dict[provider_name]
    try:
        text,total_token,prompt_token,response_token = await generate_response(model_name = details.model,
                            provider_name = provider_name,
                            user_prompt=details.prompt,
                                system_prompt=details.system_prompt,
                                temperature=details.model_temp,
                                max_tokens=details.max_tokens)
        return text,total_token,prompt_token,response_token
    except Exception as e:
        new_provider,new_model = Provider_Fallback[provider_name]
        text,total_token,prompt_token,response_token = await generate_response(model_name = new_model,
                            provider_name = new_provider,
                            user_prompt=details.prompt,
                                system_prompt=details.system_prompt,
                                temperature=details.model_temp,
                                max_tokens=details.max_tokens)
        return text,total_token,prompt_token,response_token
        
    

@retry(
    reraise=True, 
    stop=stop_after_attempt(3), 
    wait=wait_fixed(2), # we are already catching rate limits error before so those error cant come in and even if they can uhhhggg idk tbh maybe they will just run
)
async def generate_response(model_name:str ,
                            provider_name:str,
                            user_prompt :str ,
                            system_prompt:str,
                            temperature : int,
                            max_tokens:int):
    chatbot = Provider_dict[provider_name]
    text,total_token,prompt_token,response_token = await chatbot.generate(user_prompt=user_prompt,
                            system_prompt=system_prompt,
                            model_name = model_name,
                            temperature=temperature,
                            max_tokens=max_tokens)
    
    return text,total_token,prompt_token,response_token
    
