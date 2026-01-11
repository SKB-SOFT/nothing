import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./app.db")

# Use aiosqlite for async SQLite support
if "sqlite" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite:///")

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

# ==================== MODELS ====================

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    full_name = Column(String)
    is_admin = Column(Boolean, default=False)
    signup_date = Column(DateTime, default=func.now())
    quota_daily = Column(Integer, default=50)
    theme = Column(String, default='dark')

class Query(Base):
    __tablename__ = "queries"
    
    query_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False, index=True)
    query_text = Column(Text, nullable=False)
    query_timestamp = Column(DateTime, default=func.now(), index=True)
    query_type = Column(String, default='general')

class Response(Base):
    __tablename__ = "responses"
    
    response_id = Column(Integer, primary_key=True, autoincrement=True)
    query_id = Column(Integer, ForeignKey('queries.query_id'), nullable=False, index=True)
    agent_id = Column(String, nullable=False, index=True)
    response_text = Column(Text)
    response_time_ms = Column(Float)
    token_count = Column(Integer)
    status = Column(String, default='success')
    error_message = Column(Text)

class Cache(Base):
    __tablename__ = "cache"
    
    cache_id = Column(Integer, primary_key=True, autoincrement=True)
    query_hash = Column(String, unique=True, nullable=False, index=True)
    agent_id = Column(String, nullable=False, index=True)
    response_text = Column(Text)
    created_timestamp = Column(DateTime, default=func.now())

# ==================== DATABASE INITIALIZATION ====================

async def init_db():
    """Create all tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    """Get database session"""
    async with AsyncSessionLocal() as session:
        yield session
