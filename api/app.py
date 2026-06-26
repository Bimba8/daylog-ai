from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers.auth import router as auth_router
from api.routers.profile import router as profile_router
from api.routers.stats import router as stats_router


app = FastAPI(title="DayLog API")
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
