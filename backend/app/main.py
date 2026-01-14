from fastapi import FastAPI

from app.core.logging import setup_logging
from app.routers import api, webhook

setup_logging()

app = FastAPI()
app.include_router(api.router)
app.include_router(webhook.router)


@app.get("/")
def root() -> dict:
    return {"status": "ok"}
