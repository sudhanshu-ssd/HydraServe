from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from routes import auth, users, projects, chat,admin
from db import engine   
import  redis.asyncio as aioredis
import redis_config
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor,ConsoleSpanExporter

provider = TracerProvider()
processor = SimpleSpanProcessor(ConsoleSpanExporter)
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)
tracer = trace.get_tracer('hydraserve-tracer')

SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)  # note: .sync_engine — see below
RedisInstrumentor().instrument()
HTTPXClientInstrumentor().instrument()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client
    redis_config.redis_client = aioredis.Redis(host="localhost",port=6379,db=0,decode_responses=True)
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
       allow_origins=["http://localhost:5500"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )



app.include_router(auth.router)
app.include_router(users.router)
app.include_router(projects.router)
app.include_router(chat.router)
app.include_router(admin.router)




