from __future__ import annotations

from sqlalchemy.orm import mapped_column, Mapped,relationship
from sqlalchemy import String, Integer, ForeignKey,DateTime,Float
from db import Base
from datetime import datetime,UTC

class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    created_at : Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    filename : Mapped[str | None] = mapped_column(String(100),nullable=True,default=None)

    # commenting this out and below cuz alembic doesnt see this as column so either i create a column with actual s3 path now and set default to a local image path or just ignore filepath cuz filename is enough
    # @property
    # def filepath(self) -> str:
    #     if self.filename:
    #         return f"profile_pics/Pics/{self.filename}"
    #     return 'default/default_pfp_pics/Default_pfp.jpg'

    projects : Mapped[list[Project]] = relationship(back_populates="user", cascade="all, delete-orphan") 
    api_keys : Mapped[list[APIKey]] = relationship(back_populates="user", cascade="all, delete-orphan") 
    reset_password_tokens : Mapped[list[ResetPasswordToken]] = relationship(back_populates='user',cascade="all, delete-orphan")

class Project(Base):
    __tablename__ = "projects" 

    project_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(200), nullable=True , default="No description provided")
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    created_at : Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    rpm_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=50) # requests per minute limit for the project
    rpd_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=800) # requests per day limit for the project
    token_limit_day: Mapped[int] = mapped_column(Integer, nullable=False, default=100000) # token limit for the project
    token_limit_minute: Mapped[int] = mapped_column(Integer, nullable=False, default=4000) # token limit for the project

    user : Mapped[User] = relationship(back_populates="projects")
    api_keys : Mapped[list[APIKey]] = relationship(back_populates="project", cascade="all, delete-orphan")


class APIKey(Base):
    __tablename__ = "api_keys"

    api_key_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False) # hashed value of the api key
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False,index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.project_id"), nullable=False,index=True)
    api_key_created_at : Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    user : Mapped[User] = relationship(back_populates="api_keys")
    project : Mapped[Project] = relationship(back_populates="api_keys")


class Providers(Base):
    __tablename__ = 'providers'

    provider_id : Mapped[int] = mapped_column(Integer,primary_key=True,index=True)
    name : Mapped[str] = mapped_column(String(100), nullable=False)
    description : Mapped[str] = mapped_column(String(200), nullable=True,default="No description provided")
    global_rpm: Mapped[int] = mapped_column(Integer, nullable=False,default=50) # global requests per minute limit for the provider
    global_rpd: Mapped[int] = mapped_column(Integer, nullable=False,default=800) # global requests per day limit for the provider

class Logs(Base):
    __tablename__ = "logs"

    request_id : Mapped[int] = mapped_column(Integer,primary_key=True,index=True)
    user_id : Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False,index=True)
    project_id : Mapped[int] = mapped_column(ForeignKey("projects.project_id"), nullable=False,index=True)
    provider_id : Mapped[int] = mapped_column(ForeignKey("providers.provider_id"), nullable=False,index=True)
    request_time : Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    prompt_token : Mapped[int] = mapped_column(Integer,nullable=True)
    response_token : Mapped[int] = mapped_column(Integer,nullable=True)
    total_token : Mapped[int] = mapped_column(Integer,nullable=True)
    latency: Mapped[float] = mapped_column(Float,nullable=False)
    status : Mapped[str] = mapped_column(String(50),nullable=False)


class ResetPasswordToken(Base):
    __tablename__ = 'reset_password'

    reset_id : Mapped[int] = mapped_column(Integer ,primary_key=True,index=True)
    user_id : Mapped[int] = mapped_column (ForeignKey('users.user_id'),nullable=False,index=True)
    hashed_reset_token : Mapped[str] = mapped_column(String,nullable=False,unique=True)
    expires_at : Mapped[datetime] = mapped_column(DateTime(timezone=True),nullable=False)

    created_at : Mapped[datetime] = mapped_column(DateTime(timezone=True),default=lambda:datetime.now(UTC))

    user : Mapped[User] = relationship(back_populates='reset_password_tokens')