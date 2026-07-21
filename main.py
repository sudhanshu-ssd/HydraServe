from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from routes import auth, users, projects, chat
from db import engine

@asynccontextmanager
async def lifespan(_app: FastAPI):
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



app.include_router(auth.router)
app.include_router(users.router)
app.include_router(projects.router)
app.include_router(chat.router)




