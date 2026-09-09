import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.auth import router as auth_router
from app.api.v1.assistant import router as assistant_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.diagnostics import router as diagnostics_router
from app.api.v1.trainer import router as trainer_router
from app.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(title="AXIOM API", version="0.1.0")

origins = [
    "http://localhost:3000",      # для локальной разработки
    "https://relaxdev.ru",        # ВАШ ПРОДАКШЕН
    "https://www.relaxdev.ru",    # с www (опционально)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(assistant_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(diagnostics_router, prefix="/api/v1")
app.include_router(trainer_router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}
