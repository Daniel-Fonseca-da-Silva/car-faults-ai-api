import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded

from app.api.dependencies import PRODUCTION_APP_ENVS
from app.api.health import router as health_router
from app.api.lookup import router as lookup_router
from app.api.translate import router as translate_router
from app.core.config import get_settings
from app.core.rate_limit import limiter, rate_limit_exceeded_handler

settings = get_settings()

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

is_production = settings.APP_ENV in PRODUCTION_APP_ENVS

app = FastAPI(
    title="Auto Crónica AI API",
    version="1.0.0",
    description=(
        "Lean FastAPI microservice that generates structured known-issue "
        "lookups for a vehicle (brand/model/year/engine) and translates "
        "existing known issues into another locale, via a Gemini -> Groq -> "
        "OpenRouter free-tier provider chain. Consumed by the car-faults-api "
        "Nest service over POST /lookup and POST /translate with a shared "
        "Bearer API key."
    ),
    docs_url=None if is_production else "/docs",
    redoc_url=None if is_production else "/redoc",
    openapi_url=None if is_production else "/openapi.json",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

if settings.CORS_ALLOWED_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOWED_ORIGINS,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(health_router)
app.include_router(lookup_router)
app.include_router(translate_router)
