from fastapi import APIRouter,Depends,HTTPException,status
from db import get_db
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import models
from dependencies import get_current_api_bear,redis
from schema import UserPrompt,UserPromptResponse
import time
from llm import Groq_Demon
from rate import RateLimiter
import json
import hashlib
from rate import is_allowed




router = APIRouter(tags=['chat'])




def cache_user_req(prompt:str,model:str):
    data = json.dumps(
        {
            'user_prompt':prompt,
            "model":model
        },sort_keys = True              #no idea what difference sort keys make here lol
    )
    return f"cache:{hashlib.sha256(data.encode()).hexdigest()}"


@router.post('/chat',response_model=UserPromptResponse)
async def chat(user_prompt : UserPrompt,
               current_api : get_current_api_bear, # this is api auth using HTTPBearer 
               db : Annotated[AsyncSession,Depends(get_db)]
               ):

    start = time.time()
    
    pro_id = current_api.project_id

    if user_prompt.model_temp < 1:   # only cache when temp is 0,cuz above that then user want non deterministic answers so no point of cache
        prompt_cache = cache_user_req(prompt = user_prompt.prompt,model= user_prompt.model)
        data = await redis.get(prompt_cache)
        if data:
            # we need db ops here to inject logs,do that later,also need a dependency that can get us model id lol,or wait its a cache so we will add model id as info in value and extract it from there
            return json.loads(data)
        
    
    allowed,reason,member_id,model_id = is_allowed(redis_client=redis,model=user_prompt.model,project_id=pro_id,db=db)
    if not allowed:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS,detail=f"{reason} limit reached !!!!")
    
    
    prompt_token = response_token = total_token = None
    sta = 'FAILED'

    try:
        chatbot = Groq_Demon()
        response = await chatbot.generate(user_prompt.prompt)

        prompt_token = response.usage.prompt_tokens
        response_token = response.usage.completion_tokens
        total_token = response.usage.total_tokens
        sta = 'SUCCESS'
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"Error generating response: {str(e)}")
        
    finally:
        new_log = models.Logs(
            model_id = model_id,
            project_id = pro_id,
            user_id = current_api.user_id,
            prompt_token = prompt_token,
            response_token = response_token,
            total_token = total_token,
            latency = time.time() - start,
            status = sta
            )
    try:
        db.add(new_log)
        await db.commit()
    except Exception:
        await db.rollback()  

    
    return UserPromptResponse(response=response.choices[0].message.content) 