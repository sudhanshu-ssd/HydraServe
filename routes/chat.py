from fastapi import APIRouter
from dependencies import get_current_api_bear,redis,database
from schema import UserPrompt,UserPromptResponse
from services.chat_service import handle_chat_request


router = APIRouter(tags=['chat'])



@router.post('/chat',response_model=UserPromptResponse)
async def chat(details : UserPrompt,
               current_api : get_current_api_bear, # this is api auth using HTTPBearer 
               db : database,
               redis_client : redis
               ):

    text = await handle_chat_request(details=details,
                              current_api=current_api,
                              db=db,
                              redis_client=redis_client)

    
    return UserPromptResponse(response=text) 