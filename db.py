from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine,async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import os
from config import settings
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = settings.database_url.get_secret_value()

engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

asyncsessionlocal = async_sessionmaker(
    bind=engine,
    class_= AsyncSession,
    expire_on_commit=False
    )

class Base(DeclarativeBase):
    pass

async def get_db():
    async with asyncsessionlocal() as session:
        yield session



