from config import settings
import jwt
from pwdlib  import PasswordHash
from datetime import UTC,datetime,timedelta
import models
from fastapi.security import OAuth2PasswordBearer,HTTPBearer,HTTPAuthorizationCredentials,APIKeyHeader
from typing import Annotated
from fastapi import Depends,HTTPException,status
from sqlalchemy.ext.asyncio import AsyncSession
from db import get_db
from sqlalchemy import select
import hashlib
from sqlalchemy.orm import selectinload
import secrets

password_hash = PasswordHash.recommended()

oauth2_schema = OAuth2PasswordBearer(tokenUrl='/token') # this will extract the token from client request's header's authorization
httpbear = HTTPBearer(auto_error=False)   # this will also extract authorization header
api_key_header = APIKeyHeader(name="X-API-KEy",auto_error=False) # leaving this KEy typo so my Eval llm can have a field day lol 


def hash_password(password:str):
    return password_hash.hash(password)

def verify_password(password:str,hashed_password:str) -> bool:
    return password_hash.verify(password,hashed_password)


def create_access_token(data:dict,expire_time_in_minutes : timedelta | None = None):
    to_encode = data.copy()
    if expire_time_in_minutes:
        expire = datetime.now(UTC) + expire_time_in_minutes
    else:
        expire = datetime.now(UTC) + timedelta(minutes = settings.access_token_expire_minutes)
    to_encode.update({'exp':expire})
    encoded = jwt.encode(
        to_encode,
        settings.Secret_key.get_secret_value(),
        algorithm=settings.algo
    )
    return encoded


def verify_access_token(token:str) -> str :
    try:
        payload = jwt.decode(
            token,
            settings.Secret_key.get_secret_value(),
            algorithms=[settings.algo],
            options={'require':['exp','sub']}
        )
    except jwt.InvalidTokenError:
        return None
    else:
        return payload.get('sub')
    

async def get_current_user(
        token : Annotated[str,Depends(oauth2_schema)],
        db : Annotated[AsyncSession,Depends(get_db)]):
    user_id = verify_access_token(token=token)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="invalid or expired token",
                            headers={'WWW-Authenticate':'Bearer'})
    try:
        int_user_id = int(user_id)
    except (TypeError,ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="invalid or expired token",
                            headers={'WWW-Authenticate':'Bearer'})
    results = await db.execute(
        select(models.User)  # use selectinload here if you need listof apis and projects related to user 
        .options(selectinload(models.User.projects))
        .where(models.User.user_id == int_user_id)
    )
    user = results.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="User not found",
                            headers={'WWW-Authenticate':'Bearer'})
    
    return user

current_user = Annotated[models.User,Depends(get_current_user)]


def hash_api(raw_api:str) -> str:
    return hashlib.sha256(raw_api.encode()).hexdigest()


async def get_api_bear(
        incoming_api : Annotated[HTTPAuthorizationCredentials,Depends(httpbear)],
        db : Annotated[AsyncSession,Depends(get_db)]
        ) -> models.APIKey:
     
    if not incoming_api:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Request authorization header doesnt have an api key",
                            headers={"WWW-Authenticate":"Bearer"})
    hashed_incoming_api = hash_api(incoming_api.credentials)
    results = await db.execute(
        select(models.APIKey).options(selectinload(models.APIKey.project))
        .where(models.APIKey.key == hashed_incoming_api)
    )
    the_key = results.scalars().first()
    if not the_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="API KEY NOT FOUND")
    
    return the_key

async def get_api_header(
        incoming_api : Annotated[str,Depends(api_key_header)],
        db : Annotated[AsyncSession,Depends(get_db)]
        ) -> models.APIKey:  #this function is useless and was built purely for learning, in real application we wil use httpbearer
    
    if not incoming_api:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Request authorization header doesnt have an api key",
                            headers={"WWW-Authenticate":"Bearer"})
    hashed_incoming_api = hash_api(incoming_api)
    results = await db.execute(
        select(models.APIKey).options(selectinload(models.APIKey.project))
        .where(models.APIKey.key == hashed_incoming_api)
    )
    the_key = results.scalars().first()
    if not the_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="API KEY NOT FOUND")
    
    return the_key


get_current_api_bear = Annotated[models.APIKey,Depends(get_api_bear)]
get_current_api_header = Annotated[models.APIKey,Depends(get_api_header)]

async def get_project(current_api : get_current_api_bear) -> models.Project:
    #tbh we can get current project using any api as api keys cant be shared,getting user auth is necessary but for /projects we will need user auth ,
    # and tbh i am making this func purely for learn it doesnt have a purpose,and honestly this is too short

    return current_api.project


def generate_api(prefix = "hs_",length = 32):
    api_key = secrets.token_hex(length)
    return f"{prefix}{api_key}"

