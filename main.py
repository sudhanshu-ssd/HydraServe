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
from sqlalchemy.orm import selectinload
from fastapi.middleware.cors import CORSMiddleware
from botocore.exceptions import ClientError




@asynccontextmanager
async def lifespan(_app: FastAPI):
    # startup
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)
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

freq_dict = defaultdict(list)

@app.post('/token',response_model=Token)
async def sign_in_access_token(
    form_body:Annotated[OAuth2PasswordRequestForm,Depends()],
    db : Annotated[AsyncSession,Depends(get_db)]):

    sign_in_user_email = form_body.username
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



@app.post('/chat',response_model=UserPromptResponse)
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
        
        db.add(new_log)
        await db.commit()
        await db.refresh(new_log)

    
    return UserPromptResponse(response=response.choices[0].message.content) 



@app.post('/users/register',response_model=RegisterResponse,status_code=status.HTTP_201_CREATED)
async def user_register(
    user_details:UserRegister,
    db: Annotated[AsyncSession,Depends(get_db)]):
    # we will need something in the future to verify emails 

    results = await db.execute(select(models.User)
                               .where(models.User.username == user_details.username))
    users_already = results.scalars().all()
    if users_already:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Username already taken") # can we handle this at frontend??
    
    results = await db.execute(select(models.User)
                               .where(models.User.email == user_details.email.lower()))
    email_already = results.scalars().all()
    if email_already:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="email already Used") # again can we do this at frontend??
    
    new_user = models.User(
        username = user_details.username,
        email = user_details.email.lower(),
        hashed_password = hash_password(user_details.password),
        created_at = datetime.now(UTC)
        )

    db.add(new_user)
    try:
        await db.commit()
        await db.refresh(new_user) 
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=str(e))

    return RegisterResponse(username=new_user.username)



@app.post('/projects',response_model=ProjectResponse,status_code=status.HTTP_201_CREATED)
async def create_project(
    user : current_user,  # this is user auth 
    project_details : ProjectReq,  # contains name and description
    db : Annotated[AsyncSession,Depends(get_db)]):

    name = project_details.name
    des = project_details.description


    new_project = models.Project(
        name = name,
        description = des,
        user_id = user.user_id
        )

    db.add(new_project)
    try:
        await db.commit()
        await db.refresh(new_project) 
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=str(e))

    return new_project

@app.get('/projects',response_model=list[ProjectResponse])
def get_all_projects(
    user : current_user,  # this is user auth 
    ):
    return user.projects  


@app.post("/projects/{pro_id}/keys",response_model=APIresponse,status_code=status.HTTP_201_CREATED)
async def get_api_key(
    user : current_user,
    db : Annotated[AsyncSession,Depends(get_db)],
    pro_id :int
    ):

    
    results = await db.execute(
        select(models.Project)
        .where(models.Project.user_id == user.user_id , models.Project.project_id == pro_id)  #is this the right way for ownership check
    )
    if not results.scalars().first():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail= "User not authorized for this project",
                            headers={"WWW-Authenticate":"Bearer"})
    api_key = generate_api()

    hashed_api_key = hash_api(api_key)

    new_api = models.APIKey(
        key = hashed_api_key,
        project_id = pro_id,
        user_id = user.user_id
    )

    db.add(new_api)
    await db.commit()
    await db.refresh(new_api)

    return APIresponse(api_key=api_key)

@app.patch('/projects/{pro_id}', response_model=ProjectResponse ,status_code=status.HTTP_200_OK)
async def update_project(
    user : current_user,  # this is user auth 
    project_details : ProjectUpdate,  # contains name and description
    db : Annotated[AsyncSession,Depends(get_db)],
    pro_id : int):


    results = await db.execute(
        select(models.Project).
        where(models.Project.project_id == pro_id)
    )
    project = results.scalars().first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Project Not Found")
    
    if project.user_id != user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="User not authorized for this peoject")


    pro = project_details.model_dump(exclude_unset=True,)
    for key,val in pro.items():
        setattr(project,key,val)

    try:
        await db.commit()
        await db.refresh(project) 
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=str(e))

    return project

@app.delete('/projects/{pro_id}',response_model=ProjectResponse,status_code=status.HTTP_200_OK)
async def del_project(
    user : current_user,  # this is user auth 
    db : Annotated[AsyncSession,Depends(get_db)],
    pro_id : int):


    results = await db.execute(
        select(models.Project).
        where(models.Project.project_id == pro_id)
    )
    project = results.scalars().first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Project Not Found")

    if project.user_id != user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="User not authorized for this peoject")

    try:
        await db.delete(project)
        await db.commit()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=str(e))

    return project #we will just say this project has been deleted in frontend


@app.delete('/projects/{pro_id}/keys/{api_key_id}',status_code=status.HTTP_200_OK)
async def delete_api(
    user : current_user,
    db : Annotated[AsyncSession,Depends(get_db)],
    api_key_id : int,
    pro_id : int
):
    results = await db.execute(
        select(models.APIKey)
        .where(models.APIKey.api_key_id == api_key_id)
    )
    api_key = results.scalars().first()
    if not api_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail='No API KEY FOUND')
    if api_key.project_id != pro_id or api_key.user_id != user.user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="NOT YOU KEY MISTER <GET BETTER>",headers={"WWW-Authenticate":"Bearer"})
    
    try:
        await db.delete(api_key)
        await db.commit()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=str(e))
    
    return None


@app.patch('/user/profile_pic',status_code=status.HTTP_200_OK)
async def upload_profile_pic(
    user : current_user,
    db : Annotated [ AsyncSession, Depends(get_db)],
    file : UploadFile
    ):

    content = await file.read()  # content is in bytes

    if len(content) > settings.max_profile_pic_size_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Maximum image size should be 5 MB")
    
    try :
        raw_bytes,new_filename = await run_in_threadpool(process_profile_pic,content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image file. Please upload a valid image (JPEG, PNG, GIF, WebP).",
        ) from e
    
    try:
        await upload_profile_image(raw_bytes,new_filename)
    except ClientError as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload image. Please try again.",
        ) from err
    

    
    old_filename = user.filename

    user.filename = new_filename

    try:
        await db.commit()
        await db.refresh(user)

        if old_filename:
            await delete_profile_image(old_filename)

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=str(e))
    
    return None



@app.delete('/user/profile_pic' , status_code=status.HTTP_200_OK)
async def del_profile_pic(
    db : Annotated[AsyncSession,Depends(get_db)],
    user : current_user
    ):

    old_filename = user.filename

    if old_filename is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No profile picture to delete",
        )

    await delete_profile_image(old_filename)
    user.filename = None

    try:
        await db.commit()
        await db.refresh(user)

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=str(e))
    
    return None

@app.post('/users/forgot-password',status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(
    db : Annotated[AsyncSession,Depends(get_db)],  # we  cant do user auth here as user is not signed in yet and forgot the password
    background_task : BackgroundTasks,
    details : ForgotPassword
    ):

    results = await db.execute(
        select(models.User)
        .where(models.User.email == str(details.email).lower())
    )
    user = results.scalars().first()

    if user:
        await db.execute(
            delete(models.ResetPasswordToken)
            .where(models.ResetPasswordToken.user_id == user.user_id)
        )
    
        tok = generate_api(prefix="rp")  # we are generating the token from same func that we used for generating api
        hashed_token = hash_api(tok)
        expire = datetime.now(UTC) + timedelta(minutes=settings.reset_token_expire_minutes)

        reset_token = models.ResetPasswordToken(
            user_id = user.user_id,
            hashed_reset_token = hashed_token,
            expires_at = expire
        )
        db.add(reset_token)
        await db.commit()

        background_task.add_task(
            send_password_reset_email,
            to_email = user.email,
            token = tok,
            username = user.username
            )
    
    return {
        "message": "If an account exists with this email, you will receive password reset instructions.",
    }



@app.post('/reset-password',status_code=status.HTTP_200_OK)
async def reset_password(
    details : ResetPassword,
    db : Annotated[AsyncSession,Depends(get_db)],
    ):

    hashed_incoming_token = hash_api(details.token)

    results = await db.execute(
        select(models.ResetPasswordToken)
        .options(selectinload(models.ResetPasswordToken.user))
        .where(models.ResetPasswordToken.hashed_reset_token == hashed_incoming_token)
    )
    reset_token = results.scalars().first()

    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    if reset_token.expires_at < datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        ) 
    
    reset_token.user.hashed_password = hash_password(details.new_password)

    await db.execute(
        delete(models.ResetPasswordToken)
        .where(models.ResetPasswordToken.user_id == reset_token.user.user_id)
    )

    await db.commit()

    return {
        "message": "Password reset successfully. You can now log in with your new password.",
    }
    

