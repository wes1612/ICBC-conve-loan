"""FastAPI 应用入口。"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.analysis import router as analysis_router
from app.api.ai import router as ai_router
from app.api.ml import router as ml_router
from app.api.materials import router as materials_router
from app.settings import cors_origins

app = FastAPI(
    title="ICBC Consumer Supply Credit API",
    version="0.4.0",
    description="消费供给动态授信：经营评分、交易异常与资金缺口预测 MVP",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(analysis_router)
app.include_router(ml_router)
app.include_router(materials_router)
app.include_router(ai_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
