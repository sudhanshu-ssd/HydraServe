from dependencies import database
from fastapi import APIRouter,status
from schema import  Insert_Model
import models

router  = APIRouter(prefix='/admin',tags=['admin'])

@router.post('/insert_model',status_code=status.HTTP_200_OK)
async def insert_model(db : database,model_input : Insert_Model):
    # tbh idk what can be admin auth lol 
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

