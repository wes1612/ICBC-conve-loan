"""贷后全周期动态监测 API。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response

from app.schemas.demo import DemoMerchantId
from app.schemas.postloan import (
    MerchantSubmissionRequest,
    PostLoanAlert,
    PostLoanTimeline,
    ReviewDecisionRequest,
    SourceAuthorizationRequest,
)
from app.services.postloan_service import postloan_service


router = APIRouter(prefix="/api/v1/post-loan", tags=["post-loan-monitoring"])


@router.get("/merchants/{merchant_id}/timeline", response_model=PostLoanTimeline)
def merchant_timeline(
    merchant_id: DemoMerchantId,
    response: Response,
) -> PostLoanTimeline:
    """返回当前已推进月份内的贷款账户、模型结果、额度历史和数据来源。"""

    response.headers["Cache-Control"] = "no-store"
    return postloan_service.timeline(merchant_id)


@router.post("/merchants/{merchant_id}/advance-month", response_model=PostLoanTimeline)
def advance_month(merchant_id: DemoMerchantId) -> PostLoanTimeline:
    """竞赛演示专用：推进一个月并运行三引擎复评和额度状态机。"""

    return postloan_service.advance(merchant_id)


@router.post("/merchants/{merchant_id}/reset", response_model=PostLoanTimeline)
def reset_timeline(merchant_id: DemoMerchantId) -> PostLoanTimeline:
    """将指定商户恢复到贷后第一个月。"""

    return postloan_service.reset(merchant_id)


@router.post("/merchants/{merchant_id}/submissions", response_model=PostLoanTimeline)
def submit_supplement(
    merchant_id: DemoMerchantId,
    request: MerchantSubmissionRequest,
) -> PostLoanTimeline:
    """商户补充系统无法自动取得的材料或异常说明。"""

    return postloan_service.submit(merchant_id, request)


@router.post(
    "/merchants/{merchant_id}/sources/{source_id}/authorization",
    response_model=PostLoanTimeline,
)
def update_source_authorization(
    merchant_id: DemoMerchantId,
    source_id: str,
    request: SourceAuthorizationRequest,
) -> PostLoanTimeline:
    """模拟外部经营平台授权续期或撤销。"""

    try:
        return postloan_service.authorize(merchant_id, source_id, request)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/reviews/{review_id}/decision", response_model=PostLoanTimeline)
def decide_review(
    review_id: str,
    request: ReviewDecisionRequest,
) -> PostLoanTimeline:
    """银行审核端批准调整、维持原额度或升级人工复核。"""

    try:
        return postloan_service.decide(review_id, request)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/alerts", response_model=list[PostLoanAlert])
def all_alerts() -> list[PostLoanAlert]:
    return postloan_service.alerts()

