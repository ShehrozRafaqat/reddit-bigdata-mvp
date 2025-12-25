from fastapi import FastAPI

from app.db.postgres import init_db
from app.routers.auth import router as auth_router
from app.routers.health import router as health_router

app = FastAPI()

app.include_router(health_router)
app.include_router(auth_router)


@app.on_event("startup")
def startup() -> None:
    init_db()
