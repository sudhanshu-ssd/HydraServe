from fastapi import APIRouter,Depends,HTTPException,status
from db import get_db
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import models
from dependencies import current_user,generate_api,hash_api,database
from schema import ProjectReq,ProjectResponse,ProjectUpdate,APIresponse,CreateApi,ListApiKeys
from sqlalchemy.orm import selectinload

router =APIRouter(prefix='/projects',tags=['projects'])

@router.post('',response_model=ProjectResponse,status_code=status.HTTP_201_CREATED)
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

@router.get('',response_model=list[ProjectResponse])
async def get_all_projects(
    user : current_user,  # this is user auth 
    ):
    return user.projects


@router.post("/{pro_id}/keys",response_model=APIresponse,status_code=status.HTTP_201_CREATED)
async def get_api_key(
    user : current_user,
    db : Annotated[AsyncSession,Depends(get_db)],
    pro_id :int,
    api_name : CreateApi
    ):

    api_name = api_name.name
    
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
        name = api_name,
        key = hashed_api_key,
        project_id = pro_id,
        user_id = user.user_id
    )

    db.add(new_api)
    await db.commit()
    await db.refresh(new_api)

    return APIresponse(api_key=api_key)

@router.patch('/{pro_id}', response_model=ProjectResponse ,status_code=status.HTTP_200_OK)
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

@router.delete('/{pro_id}',response_model=ProjectResponse,status_code=status.HTTP_200_OK)
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
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="User not authorized for this project")

    try:
        await db.delete(project)
        await db.commit()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=str(e))

    return project #we will just say this project has been deleted in frontend


@router.delete('/{pro_id}/keys/{api_key_id}',status_code=status.HTTP_200_OK)
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


@router.get("/{project_id}/keys",response_model=list[ListApiKeys])
async def list_api_keys(
    user:current_user,
    project_id :int,
    db:database

):
    results = await db.execute(
        select(models.Project)
        .options(selectinload(models.Project.api_keys))
        .where(models.Project.project_id == project_id))

    project = results.scalars().first()

    if project.user_id != user.user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="User not authorized for this project")

    if not project:
        raise HTTPException(detail="No Project Found",status_code=status.HTTP_404_NOT_FOUND)

    

    return project.api_keys
    
    