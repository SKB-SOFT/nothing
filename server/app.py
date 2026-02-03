from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
import os
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func


from server.db import AsyncSessionLocal, User, Query, Response, Cache, init_db  # type: ignore
from server.orchestrator_v2 import (
    orchestrate_query,
    PROVIDER_CONFIGS,
    get_provider_info,
    validate_all_providers,  # ✅ added
)
from server.routes.dashboard import router as dashboard_router  # type: ignore

from dotenv import load_dotenv
import asyncio
from contextlib import asynccontextmanager

_ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(_ENV_PATH)

# Initialize database with lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown (if needed)

# FastAPI app
app = FastAPI(
    title="Multi-AI Orchestrator API",
    version="1.0.0",
    description="Query multiple AI models simultaneously with caching",
    lifespan=lifespan
)

# Setup
security = HTTPBearer(auto_error=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this")
ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", 24))

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://*.vercel.app", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include dashboard routes
app.include_router(dashboard_router)

# ==================== PYDANTIC MODELS ====================

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class QueryRequest(BaseModel):
    query_text: str
    # Defaults must exist in PROVIDER_CONFIGS (orchestrator_v2)
    selected_agents: List[str] = ["groq", "gemini", "mistral", "cerebras", "cohere", "huggingface"]

# ==================== DEPENDENCIES ====================

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Validate JWT and return current user"""
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Return a user when a valid Bearer token is present; otherwise None."""
    if credentials is None:
        return None

    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            return None

        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        return user
    except Exception:
        return None


async def get_or_create_guest_user(db: AsyncSession) -> User:
    """Ensure a stable guest user exists for unauthenticated usage."""
    guest_email = os.getenv("GUEST_EMAIL", "guest@local")
    result = await db.execute(select(User).where(User.email == guest_email))
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    guest = User(
        email=guest_email,
        password_hash=get_password_hash(os.getenv("GUEST_PASSWORD", "guest")),
        full_name=os.getenv("GUEST_FULL_NAME", "Guest"),
        quota_daily=int(os.getenv("GUEST_QUOTA_DAILY", "1000000")),
        is_admin=False,
    )
    db.add(guest)
    await db.commit()
    await db.refresh(guest)
    return guest

# ==================== AUTH ENDPOINTS ====================

@app.post("/api/auth/register")
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        full_name=user_data.full_name,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    access_token = create_access_token(data={"sub": new_user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": new_user.user_id,
            "email": new_user.email,
            "full_name": new_user.full_name,
            "quota_daily": new_user.quota_daily,
        }
    }

@app.post("/api/auth/login")
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = create_access_token(data={"sub": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.user_id,
            "email": user.email,
            "full_name": user.full_name,
            "quota_daily": user.quota_daily,
        }
    }

@app.get("/api/auth/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "user": {
            "id": current_user.user_id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "quota_daily": current_user.quota_daily,
            "is_admin": current_user.is_admin,
        }
    }

@app.get("/api/providers")
async def list_providers():
    """Return provider initialization status and defaults."""
    return {"providers": get_provider_info()}

@app.get("/api/providers/validate")
async def providers_validate():
    """
    Actively calls each initialized provider with a tiny prompt and returns pass/fail + reason.
    """
    from server.orchestrator_v2 import PROVIDERS  # ensures we reference the live registry

    info = get_provider_info()
    out = {}

    # Call each provider directly so we can return error_type + error_message
    for pid, provider in PROVIDERS.items():
        try:
            r = await provider.query("Hello", timeout=12)
            out[pid] = {
                "ok": r.get("status") == "success",
                "status": info.get(pid, {}).get("status"),
                "default_model": info.get(pid, {}).get("default_model"),
                "error_type": r.get("error_type"),
                "error_message": r.get("error_message"),
            }
        except Exception as e:
            out[pid] = {
                "ok": False,
                "status": info.get(pid, {}).get("status"),
                "default_model": info.get(pid, {}).get("default_model"),
                "error_type": "exception",
                "error_message": str(e)[:160],
            }

    return {"results": out}

# ==================== QUERY ENDPOINTS ====================

@app.post("/api/query")
async def submit_query(
    query_data: QueryRequest,
    current_user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db)
):
    user = current_user
    if user is None:
        user = await get_or_create_guest_user(db)

    if len(query_data.query_text.strip()) < 5:
        raise HTTPException(status_code=400, detail="Query too short (min 5 chars)")
    if len(query_data.query_text) > 5000:
        raise HTTPException(status_code=400, detail="Query too long (max 5000 chars)")

    today = datetime.now(timezone.utc).date()
    today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)

    result = await db.execute(
        select(func.count(Query.query_id)).where(
            (Query.user_id == user.user_id) &
            (Query.query_timestamp >= today_start)
        )
    )
    today_count = result.scalar() or 0

    if today_count >= user.quota_daily:
        raise HTTPException(status_code=429, detail="Daily quota exceeded")

    for agent_id in query_data.selected_agents:
        if agent_id not in PROVIDER_CONFIGS:
            raise HTTPException(status_code=400, detail=f"Unknown agent: {agent_id}")

    new_query = Query(
        user_id=user.user_id,
        query_text=query_data.query_text,
        query_type="general"
    )
    db.add(new_query)
    await db.flush()

    orch_result = await orchestrate_query(
        user.user_id,
        query_data.query_text,
        query_data.selected_agents,
        db
    )

    for provider_id, response_data in orch_result["responses"].items():
        db_response = Response(
            query_id=new_query.query_id,
            agent_id=provider_id,
            response_text=response_data.get("response_text", ""),
            response_time_ms=response_data.get("response_time_ms", 0),
            token_count=response_data.get("token_count", 0),
            status=response_data["status"],
            error_message=response_data.get("error_message"),
        )
        db.add(db_response)

    await db.commit()
    await db.refresh(new_query)

    responses_list = [
        {
            "agent_id": provider_id,
            "agent_name": PROVIDER_CONFIGS.get(provider_id, {}).get("name", provider_id),
            **response_data
        }
        for provider_id, response_data in orch_result["responses"].items()
    ]

    final_answer = orch_result.get("final_answer") or "No provider succeeded. Try again."

    errors = [
        {
            "agent_id": r.get("agent_id"),
            "error_type": r.get("error_type"),
            "error_message": r.get("error_message"),
        }
        for r in responses_list
        if r.get("status") == "error"
    ]

    return {
        "query_id": new_query.query_id,
        "query_text": new_query.query_text,
        "timestamp": new_query.query_timestamp.isoformat(),
        "final_answer": final_answer,
        "errors": errors,
        "responses": responses_list,
        "metadata": {
            **orch_result.get("metadata", {}),
            "queries_remaining": max(0, user.quota_daily - today_count - 1),
        }
    }

@app.get("/api/queries")
async def get_user_queries(
    db: AsyncSession = Depends(get_db),
    limit: int = 20,
    offset: int = 0,
    current_user: User | None = Depends(get_optional_user),
):
    # If not authenticated, fallback to guest user (like /api/query)
    user = current_user
    if user is None:
        user = await get_or_create_guest_user(db)

    result = await db.execute(
        select(Query)
        .where(Query.user_id == user.user_id)
        .order_by(Query.query_timestamp.desc())
        .limit(limit)
        .offset(offset)
    )
    queries = result.scalars().all()

    queries_data = []
    for q in queries:
        result = await db.execute(select(Response).where(Response.query_id == q.query_id))
        responses = result.scalars().all()

        queries_data.append({
            "query_id": q.query_id,
            "query_text": q.query_text[:100],
            "timestamp": q.query_timestamp.isoformat(),
            "response_count": len(responses),
        })

    return {"queries": queries_data}

@app.get("/api/query/{query_id}")
async def get_query_details(
    query_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Query).where(
            (Query.query_id == query_id) & (Query.user_id == current_user.user_id)
        )
    )
    query = result.scalar_one_or_none()

    if not query:
        raise HTTPException(status_code=404, detail="Query not found")

    result = await db.execute(select(Response).where(Response.query_id == query_id))
    responses = result.scalars().all()

    return {
        "query_id": query.query_id,
        "query_text": query.query_text,
        "timestamp": query.query_timestamp.isoformat(),
        "responses": [
            {
                "response_id": r.response_id,
                "agent_id": r.agent_id,
                "agent_name": PROVIDER_CONFIGS.get(r.agent_id, {}).get("name", r.agent_id),
                "response_text": r.response_text,
                "response_time_ms": r.response_time_ms,
                "token_count": r.token_count,
                "status": r.status,
                "error_message": r.error_message,
            }
            for r in responses
        ]
    }

@app.get("/api/admin/users")
async def get_all_users(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 10,
    offset: int = 0
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    result = await db.execute(select(User).limit(limit).offset(offset))
    users = result.scalars().all()

    users_data = []
    for user in users:
        result = await db.execute(select(func.count(Query.query_id)).where(Query.user_id == user.user_id))
        query_count = result.scalar() or 0

        users_data.append({
            "user_id": user.user_id,
            "email": user.email,
            "full_name": user.full_name,
            "signup_date": user.signup_date.isoformat() if user.signup_date else None,
            "total_queries": query_count,
            "quota_daily": user.quota_daily,
            "is_admin": user.is_admin,
        })

    return {"users": users_data}

@app.get("/api/admin/metrics")
async def get_metrics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    total_users = await db.execute(select(func.count(User.user_id)))
    total_users = total_users.scalar() or 0

    total_queries = await db.execute(select(func.count(Query.query_id)))
    total_queries = total_queries.scalar() or 0

    result = await db.execute(select(func.avg(Response.response_time_ms)))
    avg_response_time = result.scalar() or 0

    return {
        "total_users": total_users,
        "total_queries": total_queries,
        "avg_response_time_ms": float(avg_response_time or 0),
        "models": PROVIDER_CONFIGS,
    }

@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/")
async def root():
    return {
        "name": "Multi-AI Orchestrator API",
        "version": "1.0.0",
        "docs": "/docs",
        "models": list(PROVIDER_CONFIGS.keys())
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
