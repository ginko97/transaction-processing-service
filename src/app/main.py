from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .core.config import get_settings
from .core.logger import setup_logging, logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Service starting up", extra={"env": get_settings().ENVIRONMENT})
    yield
    logger.info("Service shutting down")


app = FastAPI(
    title=get_settings().APP_NAME,
    version=get_settings().VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "environment": get_settings().ENVIRONMENT,
        "version": get_settings().VERSION,
    }


@app.get("/")
async def root():
    return {"message": "Transaction Processing Service is running"}
