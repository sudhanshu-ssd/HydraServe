from fastapi import FastAPI
from app_state import APP_START_TIME
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
 
import  redis.asyncio as aioredis
import redis_config
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor,ConsoleSpanExporter,BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from config import settings
from urllib.parse import unquote
from prometheus_client import make_asgi_app



resource = Resource.create({
    'service.name':"hydraserve",
    "service.version":"1.0.0",
    "deployment.environment": "development"
    })

provider = TracerProvider(resource=resource)

headers = {}
if settings.OTEL_Exporter_OTLP_Headers:
    headers["Authorization"] = unquote(settings.OTEL_Exporter_OTLP_Headers.replace("Authorization=",""))

otlp_exporter = OTLPSpanExporter(
    endpoint=settings.OTEL_Exporter_OTLP_Endpoint + "/v1/traces",
    headers=headers
)

provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
trace.set_tracer_provider(provider)


from routes import auth, users, projects, chat,admin,health,dashboard,mod
from db import engine  

SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)  
RedisInstrumentor().instrument()
HTTPXClientInstrumentor().instrument()




@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client
    redis_config.redis_client = aioredis.Redis.from_url(settings.redis_url, decode_responses=True)  
    pong = await redis_config.redis_client.ping()
    print(f"Redis connected: {pong}")  
    yield
    # closeup
    await engine.dispose()
    await redis_config.redis_client.aclose()

app = FastAPI(lifespan=lifespan)

FastAPIInstrumentor.instrument_app(app)


app.add_middleware(
       CORSMiddleware,
       allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )



app.include_router(auth.router)
app.include_router(users.router)
app.include_router(projects.router)
app.include_router(chat.router)
app.include_router(admin.router)
app.include_router(health.router)
app.include_router(dashboard.router)
app.include_router(mod.router)

metrics_app = make_asgi_app()

app.mount("/metrics", metrics_app)




