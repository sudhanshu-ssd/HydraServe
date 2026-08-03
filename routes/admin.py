from dependencies import database
from fastapi import APIRouter, status, Depends, HTTPException, Header
from schema import Insert_Model
import models
from config import settings

router = APIRouter(prefix='/admin', tags=['admin'])

async def verify_admin(x_admin_key: str = Header(...)):
    if x_admin_key != settings.admin_api_key.get_secret_value():
        raise HTTPException(status_code=401, detail="Invalid Admin Key")

@router.post('/insert_model', status_code=status.HTTP_200_OK, dependencies=[Depends(verify_admin)])
async def insert_model(db: database, model_input: Insert_Model):
    new_model = models.Models(
        model_name = model_input.model_name,
        global_rpm = model_input.g_rpm,
        global_rpd =  model_input.g_rpd,
        global_tpm =  model_input.g_tpm,
        global_tpd =  model_input.g_tpd,
        provider_id = model_input.provider_id
        )
    db.add(new_model)
    await db.commit()
    await db.refresh(new_model)

