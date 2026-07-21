from fastapi import APIRouter,Depends,HTTPException,status
from db import get_db
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import models
from dependencies import get_current_api_bear
from schema import UserPrompt,UserPromptResponse
from collections import defaultdict
import time
from llm import Groq_Demon
from rate import RateLimiter



router = APIRouter(tags=['chat'])


freq_dict = defaultdict(list)


@router.post('/chat',response_model=UserPromptResponse)
async def chat(user_prompt : UserPrompt,
               current_api : get_current_api_bear, # this is api auth using HTTPBearer 
               db : Annotated[AsyncSession,Depends(get_db)]
               ):

    start = time.time()
    
    project_id = current_api.project_id
    provider_id = 1 # will add db extrction later
    
    
    chatbot = Groq_Demon()
    
    limiter = RateLimiter()
    if not await limiter.is_allowed(project_id,freq_dict):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS,detail="Rate limit exceeded. Please try again later.")
    
    prompt_token = response_token = total_token = None
    sta = 'FAILED'
    try:
        response = await chatbot.generate(user_prompt.prompt)
        await limiter.update_usage(project_id,response.usage.total_tokens,freq_dict)

        prompt_token = response.usage.prompt_tokens
        response_token = response.usage.completion_tokens
        total_token = response.usage.total_tokens
        sta = 'SUCCESS'
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"Error generating response: {str(e)}")
        
    finally:
        new_log = models.Logs(
            provider_id = provider_id,
            project_id = project_id,
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