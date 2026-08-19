"""申请材料上传、模拟解析和演示文件下载接口。"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.schemas.material import MaterialEvidence, MaterialGroup, MaterialParseRequest
from app.services.material_service import parse_material


router = APIRouter(prefix="/api/v1/materials", tags=["application-materials"])
REPO_ROOT = Path(__file__).resolve().parents[3]

DEMO_FILES: dict[tuple[str, MaterialGroup], Path] = {
    (merchant_id, group): path
    for merchant_id in ("M001", "M005")
    for group, path in {
        "license": REPO_ROOT / "output" / "pdf" / "demo_materials" / merchant_id / f"{merchant_id}_business_license.pdf",
        "cashflow": REPO_ROOT / "outputs" / "material_upload_demo" / merchant_id / f"{merchant_id}_cashflow_12m.xlsx",
        "statement": REPO_ROOT / "output" / "pdf" / "demo_materials" / merchant_id / f"{merchant_id}_financial_statement.pdf",
        "tax": REPO_ROOT / "outputs" / "material_upload_demo" / merchant_id / f"{merchant_id}_tax_invoice_12m.xlsx",
        "plan": REPO_ROOT / "output" / "pdf" / "demo_materials" / merchant_id / f"{merchant_id}_business_plan.pdf",
        "asset": REPO_ROOT / "output" / "pdf" / "demo_materials" / merchant_id / f"{merchant_id}_lease_asset_proof.pdf",
    }.items()
}


@router.post("/parse", response_model=MaterialEvidence)
def parse_uploaded_material(request: MaterialParseRequest) -> MaterialEvidence:
    """校验真实上传文件，并按竞赛案例返回明确标注的模拟解析摘要。"""

    try:
        return parse_material(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/demo/{merchant_id}/{group}")
def download_demo_material(merchant_id: str, group: MaterialGroup) -> FileResponse:
    """下载仓库内置的 M001/M005 演示材料。"""

    path = DEMO_FILES.get((merchant_id, group))
    if path is None or not path.is_file():
        raise HTTPException(status_code=404, detail="演示材料尚未生成或不存在")
    return FileResponse(path, filename=path.name)

