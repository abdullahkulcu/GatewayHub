from fastapi import FastAPI

from app.config import get_settings

app = FastAPI(title="GatewayHub")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    get_settings()
    return {"status": "ok"}
