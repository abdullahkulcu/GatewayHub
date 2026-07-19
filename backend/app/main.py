from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.settings import router as settings_router
from app.api.tasks import router as tasks_router
from app.api.users import router as users_router
from app.bootstrap import ensure_bootstrap_admin
from app.config import get_settings
from app.db import SessionLocal


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    with SessionLocal() as db:
        ensure_bootstrap_admin(db)
    yield


app = FastAPI(title="GatewayHub", lifespan=lifespan)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(settings_router)
app.include_router(tasks_router)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    get_settings()
    return {"status": "ok"}
