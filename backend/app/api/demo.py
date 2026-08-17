"""Randomized website demonstrations backed by the five simulated merchants."""

from __future__ import annotations

from fastapi import APIRouter, Query, Response

from app.schemas.demo import DemoCasePayload, DemoMerchantId
from app.services.demo_service import get_demo_case, random_demo_case


router = APIRouter(prefix="/api/v1/demo", tags=["simulated-demonstrations"])


@router.get("/cases/random", response_model=DemoCasePayload)
def random_case(
    response: Response,
    exclude: DemoMerchantId | None = Query(default=None),
) -> DemoCasePayload:
    response.headers["Cache-Control"] = "no-store"
    return random_demo_case(exclude)


@router.get("/cases/{merchant_id}", response_model=DemoCasePayload)
def case_by_id(merchant_id: DemoMerchantId) -> DemoCasePayload:
    return get_demo_case(merchant_id)

