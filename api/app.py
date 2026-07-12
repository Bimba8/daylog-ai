from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from api.routers.auth import router as auth_router
from api.routers.profile import router as profile_router
from api.routers.stats import router as stats_router
from bot.services.ai import ai_router
from api.rate_limiter import APIRateLimitMiddleware
from config import config


@asynccontextmanager
async def lifespan(app: FastAPI):
    await ai_router.start()
    yield
    await ai_router.close()

_allowed_origins = [o.strip() for o in config.WEBAPP_URL.split(",") if o.strip()] if config.WEBAPP_URL else []

app = FastAPI(title="DayLog API", lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)

# Rate Limiter (Redis-based) — регистрируется ДО CORS,
# чтобы выполняться ПОСЛЕ CORS в стеке middleware Starlette
app.add_middleware(APIRateLimitMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH"],
    allow_headers=["Authorization", "Content-Type"]
)

app.include_router(auth_router, prefix="/api")
app.include_router(profile_router, prefix="/api")
app.include_router(stats_router, prefix="/api")

@app.get("/health")
def test():
    return {"status": "ok"}
