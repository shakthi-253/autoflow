import os
import logging

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.database import Base, engine
from app.models import vehicle, service  # noqa: F401 - ensures models are registered
from app.routers import vehicles, services
from app.services.exceptions import AppError

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("autoflow")

DEBUG = os.getenv("DEBUG", "false").lower() == "true"

app = FastAPI(title="AutoFlow API", version="1.0.0")

cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in cors_origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.exception_handler(AppError)
def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details,
        },
    )


@app.exception_handler(RequestValidationError)
def validation_error_handler(request: Request, exc: RequestValidationError):
    # Flatten pydantic's error format into something simple for the frontend.
    errors = [
        {"field": ".".join(str(p) for p in err["loc"] if p != "body"), "message": err["msg"]}
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={
            "error": "VALIDATION_ERROR",
            "message": "One or more fields are invalid",
            "details": {"errors": errors},
        },
    )


@app.exception_handler(Exception)
def unhandled_exception_handler(request: Request, exc: Exception):
    # Never leak raw stack traces to the client.
    logger.exception("Unhandled error while processing request")
    content = {"error": "INTERNAL_ERROR", "message": "An unexpected error occurred", "details": None}
    if DEBUG:
        content["details"] = {"exception": str(exc)}
    return JSONResponse(status_code=500, content=content)


app.include_router(vehicles.router)
app.include_router(services.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
