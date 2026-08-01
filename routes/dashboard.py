from dependencies import database,current_user
from sqlalchemy import  select,func,case,desc
from fastapi import APIRouter
from schema import DashOverview,RequestHistoryItem,modelusage,TokenTrend,RequestTrend
import models
from datetime import date,timedelta
from sqlalchemy.orm import selectinload

router = APIRouter(tags=['dashboard'],prefix='/dashboard')

@router.get("/overview",response_model=DashOverview)
async def dash_overview(
    user : current_user,
    db : database
):
    num_keys = len(user.api_keys)
    num_projects = len(user.projects)

    today = date.today()

    query = (select(
        func.count(case((models.Logs.created_at >= today,1),else_=None)).label('req_today'),

        func.sum(case((models.Logs.created_at >= today,models.Logs.total_token),else_= 0)).label('tokens_today'),

        func.avg(models.Logs.latency).label('avg_latency'),

        func.count(case((models.Logs.status == "CACHED",1),else_=None)).label('cache_hits'),

        func.count(case((models.Logs.status == "SUCCESS",1),else_=None)).label("success_req")
    ).where(models.Logs.user_id == user.user_id))

    results= await db.execute(query)
    stats = results.mappings().one()

    num_req = stats["req_today"] or 0
    num_tokens = stats["tokens_today"] or 0
    avg_latency = stats["avg_latency"] or 0.0
    cache_hit_num = stats["cache_hits"] or 0
    success_req = stats['success_req'] or 0

        # Calculate percentage safely in Python
    ch_percent = (cache_hit_num * 100) / num_req if num_req > 0 else 0.0
    s_percent = (success_req * 100) / num_req if num_req > 0 else 0.0

    return DashOverview(
            projects=num_projects,
            api_keys=num_keys,
            requests_today=num_req,
            tokens_today=num_tokens,
            avg_latency=round(avg_latency,2),
            cache_hit_rate=round(ch_percent,2),
            success_rate = round(s_percent,2)
    )


@router.get('/request-history',response_model=list[RequestHistoryItem])
async def get_req_history(
    db:database,
    user : current_user
):
    latest_logs_query = (
    select(models.Logs).options(selectinload(models.Logs.model).selectinload(models.Models.provider))
    .where(models.Logs.user_id == user.user_id)
    .order_by(desc(models.Logs.created_at))  # Newest first
    .limit(30)
    )
    result = await db.execute(latest_logs_query)
    latest_logs = result.scalars().all()

    model_provider = []
    for logs in latest_logs:
        model = logs.model.model_name
        provider = logs.model.provider.name
        request_time = logs.created_at
        latency = logs.latency
        tokens = logs.total_token
        status = logs.status
        model_provider.append(RequestHistoryItem(request_time=request_time,provider=provider,model=model,latency=latency,tokens=tokens,status=status))


    return model_provider


@router.get('/model-usage',response_model=list[modelusage]) #model usage has model name, tokens and req count
async def model_usage(
    db:database,
    user : current_user
):
    query = (
        select(
            models.Models.model_name.label('model_name'),  
            func.count(models.Logs.request_id).label('requests'),
            func.sum(models.Logs.total_token).label('tokens')
        ).join(
            models.Models,
            models.Models.model_id == models.Logs.model_id
        )
        .where(models.Logs.user_id == user.user_id)
        .group_by(models.Models.model_name)
    )

    result = await db.execute(query)
    rows = result.mappings().all()   # this is list of dicts 

    return [
        modelusage(
            model=row["model_name"],
            token=row["tokens"],
            requests=row["requests"]
            )
            for row in rows
            ]



@router.get("/token-trend", response_model=list[TokenTrend])
async def token_trend(
    db: database,
    user: current_user
):
    seven_days = date.today() - timedelta(days=6)

    query = (
        select(
            func.date(models.Logs.created_at).label("day"),
            func.sum(models.Logs.total_token).label("tokens")
        )
        .where(
            models.Logs.user_id == user.user_id,
            models.Logs.created_at >= seven_days
        )
        .group_by(func.date(models.Logs.created_at))
        .order_by(func.date(models.Logs.created_at))
    )

    rows = (await db.execute(query)).mappings().all()

    return [
        TokenTrend(
            day=row["day"],
            tokens=row["tokens"] or 0
        )
        for row in rows
    ]


@router.get("/request-trend", response_model=list[RequestTrend])
async def request_trend(
    db: database,
    user: current_user
):
    seven_days = date.today() - timedelta(days=6)

    query = (
        select(
            func.date(models.Logs.created_at).label("day"),
            func.count(models.Logs.request_id).label("requests")
        )
        .where(
            models.Logs.user_id == user.user_id,
            models.Logs.created_at >= seven_days
        )
        .group_by(func.date(models.Logs.created_at))
        .order_by(func.date(models.Logs.created_at))
    )

    rows = (await db.execute(query)).mappings().all()

    return [
        RequestTrend(
            day=row["day"],
            requests=row["requests"]
        )
        for row in rows
    ]





    


    
