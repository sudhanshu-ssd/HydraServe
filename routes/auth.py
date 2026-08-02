from fastapi import APIRouter,Depends,HTTPException,status
from db import get_db
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm
from schema import Token
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import models
from dependencies import verify_password,create_access_token
from datetime import timedelta
from config import settings

router = APIRouter(tags=['auth'])

@router.post('/token',response_model=Token)
async def sign_in_access_token(
    form_body:Annotated[OAuth2PasswordRequestForm,Depends()],
    db : Annotated[AsyncSession,Depends(get_db)]):

    sign_in_user_email = str(form_body.username).lower()
    results = await db.execute(
        select(models.User)
        .where(models.User.email == sign_in_user_email))
    
    user = results.scalars().first()

    if not user or not verify_password(form_body.password,user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="password or email is not correct",
                            headers={'WWW-Authenticate':"Bearer"}) 
    
    data={'sub':str(user.user_id)}
    expire = timedelta(minutes = settings.access_token_expire_minutes)
    token = create_access_token(
        data=data,
        expire_time_in_minutes=expire
        )
    return Token(access_token = token,token_type = "Bearer")