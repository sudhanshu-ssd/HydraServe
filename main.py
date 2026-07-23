from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from routes import auth, users, projects, chat,admin
from db import engine   
import  redis.asyncio as aioredis
import redis_config

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




