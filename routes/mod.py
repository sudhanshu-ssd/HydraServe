from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.orm import selectinload

import models
from dependencies import database,current_user
from schema import ModelResponse

router = APIRouter(
    prefix="/models",
    tags=["models"]
)

@router.get("", response_model=list[ModelResponse])
async def list_models(
    db: database,
    user: current_user      # keep auth so only logged in users can view
):
    result = await db.execute(
        select(models.Models)
        .options(selectinload(models.Models.provider))
    )

    models_list = result.scalars().all()

    return [
        ModelResponse(
            model_id=m.model_id,
            model_name=m.model_name,
            provider=m.provider.name
        )
        for m in models_list
    ]