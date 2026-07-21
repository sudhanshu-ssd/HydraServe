from collections import defaultdict
from fastapi import FastAPI,Depends,HTTPException,status,UploadFile,BackgroundTasks
import models
from contextlib import asynccontextmanager
from db import engine, Base,get_db
from schema import UserPrompt,UserPromptResponse,Token,RegisterResponse,UserRegister,ProjectResponse,ProjectReq,APIresponse,ProjectUpdate,ForgotPassword,ChangePassword,ResetPassword
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,delete
from llm import Groq_Demon
from rate import RateLimiter
from fastapi.security import OAuth2PasswordRequestForm
from auth import verify_password,create_access_token,current_user,hash_api,hash_password,get_current_api_bear,generate_api
from datetime import timedelta,datetime,UTC
from config import settings
import time
from starlette.concurrency import run_in_threadpool
from img_utils import process_profile_pic,delete_profile_image,upload_profile_image
from email_utils import send_password_reset_email
from fastapi.middleware.cors import CORSMiddleware
from botocore.exceptions import ClientError




@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield
    # closeup
    await engine.dispose()

app = FastAPI(lifespan=lifespan)


app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:5500"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )









