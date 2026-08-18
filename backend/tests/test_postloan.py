from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.postloan import (
    MerchantSubmissionRequest,
    ReviewDecisionRequest,
    SourceAuthorizationRequest,
)
from app.services.postloan_service import postloan_service


client = TestClient(app)


def _advance_to(merchant_id: str, month_index: int):
    timeline = postloan_service.reset(merchant_id)  # type: ignore[arg-type]
    while timeline.current_month_index < month_index:
        timeline = postloan_service.advance(merchant_id)  # type: ignore[arg-type]
    return timeline


def test_monthly_timeline_has_provenance_and_no_future_snapshots() -> None:
    timeline = _advance_to("M001", 3)

    assert timeline.current_month_index == 3
    assert len(timeline.snapshots) == 3
    assert [item.month_index for item in timeline.snapshots] == [1, 2, 3]
    assert all(item.month <= timeline.as_of_month for item in timeline.snapshots)
    assert all(
        submission.submitted_at.date() <= timeline.snapshots[-1].observed_at.date()
        for submission in timeline.submissions
    )
    assert {
        "BANK_INTERNAL_SIMULATED",
        "PLATFORM_AUTHORIZED_SIMULATED",
        "MERCHANT_SUBMITTED_SIMULATED",
        "MANUAL_VERIFIED_SIMULATED",
    } == {item.source_type for item in timeline.source_statuses}
    assert timeline.current_review.action == "INCREASE"
    assert "REPAYMENT_GOOD_3M" in timeline.current_review.reason_codes


def test_five_deterministic_scenarios_reach_expected_policy_actions() -> None:
    assert _advance_to("M002", 3).current_review.action == "INCREASE"
    assert _advance_to("M003", 3).current_review.action == "DECREASE"
    assert _advance_to("M004", 3).current_review.action == "MANUAL_REVIEW"

    abnormal = _advance_to("M005", 1)
    assert abnormal.current_review.action == "FREEZE"
    assert abnormal.loan_account.status == "FROZEN"
    assert abnormal.loan_account.available_limit == 0


def test_approved_limit_change_respects_outstanding_and_updates_account() -> None:
    timeline = _advance_to("M001", 3)
    review = timeline.current_review
    approved = postloan_service.decide(
        review.review_id,
        ReviewDecisionRequest(
            decision="APPROVE",
            approved_limit=review.proposed_limit,
            note="test approval",
        ),
    )

    assert approved.current_review.status == "APPROVED"
    assert approved.loan_account.current_limit == review.proposed_limit
    assert approved.loan_account.current_limit >= approved.loan_account.outstanding_principal
    assert approved.loan_account.current_limit <= review.current_limit * 1.15


def test_expired_platform_authorization_can_be_renewed() -> None:
    timeline = _advance_to("M004", 3)
    platform = next(
        item for item in timeline.source_statuses if item.source_id == "platform_meituan"
    )
    assert platform.authorization_status == "EXPIRED"

    renewed = postloan_service.authorize(
        "M004",
        "platform_meituan",
        SourceAuthorizationRequest(action="RENEW", expires_at=date(2027, 12, 31)),
    )
    platform = next(
        item for item in renewed.source_statuses if item.source_id == "platform_meituan"
    )
    assert platform.authorization_status == "ACTIVE"
    assert platform.quality_status == "VERIFIED"


def test_merchant_supplement_is_reported_but_not_auto_verified() -> None:
    postloan_service.reset("M001")
    timeline = postloan_service.submit(
        "M001",
        MerchantSubmissionRequest(
            category="PURPOSE_PROOF",
            description="补充本月设备采购发票和资金用途说明。",
            file_name="equipment_invoice_demo.pdf",
        ),
    )

    submission = timeline.submissions[-1]
    assert submission.verification_status == "PENDING"
    assert submission.source_type == "MERCHANT_SUBMITTED_SIMULATED"
    assert timeline.loan_account.current_limit == timeline.loan_account.initial_limit


def test_postloan_http_endpoints_expose_timeline_and_advance() -> None:
    postloan_service.reset("M002")
    response = client.get("/api/v1/post-loan/merchants/M002/timeline")
    assert response.status_code == 200
    assert response.json()["current_month_index"] == 1
    assert response.headers["cache-control"] == "no-store"

    response = client.post("/api/v1/post-loan/merchants/M002/advance-month")
    assert response.status_code == 200
    assert response.json()["current_month_index"] == 2
