from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from api.routers.auth import router as auth_router
from api.routers.profile import router as profile_router
from api.routers.stats import router as stats_router
from bot.services.ai import ai_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await ai_router.start()
    yield
    await ai_router.close()

app = FastAPI(title="DayLog API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # НАДО ВСТАВИТЬ АКТУАЛЬНЫЙ ДОМЕН ФРОНТЕНДА 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(auth_router, prefix="/api")
app.include_router(profile_router, prefix="/api")
app.include_router(stats_router, prefix="/api")

@app.get("/health")
def test():
    return {"status": "ok"}
