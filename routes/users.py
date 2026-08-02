from fastapi import APIRouter,Depends,HTTPException,status,UploadFile,BackgroundTasks
from db import get_db
from typing import Annotated
from schema import UserRegister,RegisterResponse,ForgotPassword,ResetPassword
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,delete
import models
from dependencies import hash_password,current_user,generate_api,hash_api
from datetime import timedelta,datetime,UTC
from config import settings
from img_utils import process_profile_pic,upload_profile_image,delete_profile_image
from starlette.concurrency import run_in_threadpool
from botocore.exceptions import ClientError 
from email_utils import send_password_reset_email
from sqlalchemy.orm import selectinload


router = APIRouter(prefix = "/users",tags=['auth'])

@router.post('/register',response_model=RegisterResponse,status_code=status.HTTP_201_CREATED)
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


@router.patch('/profile_pic',status_code=status.HTTP_200_OK)
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



@router.delete('/profile_pic' , status_code=status.HTTP_200_OK)
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

@router.post('/forgot-password',status_code=status.HTTP_202_ACCEPTED)
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



@router.post('/reset-password',status_code=status.HTTP_200_OK)
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


@router.get("/me")
async def get_username(
    user:current_user
):
    return {'username':user.username,"profile_pic":f"s3://hydraserve-api/profile_pics/{user.filename}"}