from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.auth import router as auth_router
from app.api.settings import router as settings_router
from app.api.tasks import router as tasks_router
from app.api.users import router as users_router
from app.bootstrap import ensure_bootstrap_admin
from app.config import get_settings
from app.db import SessionLocal

FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"


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


# Serves the built frontend (`npm run build` in frontend/) as static files,
# with an SPA fallback so client-side routes (e.g. /change-password) don't
# 404 on a hard reload. Registered last so it never shadows the API routes
# above. Skipped entirely when the frontend hasn't been built (e.g. backend
# tests), so it never interferes with those.
if FRONTEND_DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str) -> FileResponse:
        return FileResponse(FRONTEND_DIST / "index.html")
