from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.config import get_settings
from app.db import Base, engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    # For a portfolio project create_all is enough; swap in Alembic for real migrations.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=get_settings().app_name, version="0.1.0", lifespan=lifespan)
app.include_router(router)
