"""校验文件并返回可复现的竞赛模拟解析结果。"""

from __future__ import annotations

import base64
import binascii
import hashlib
from pathlib import Path
from typing import Any

from app.schemas.material import MaterialEvidence, MaterialParseRequest
from app.services.document_reader import DocumentExtraction, read_document


ALLOWED_EXTENSIONS = {
    "license": {".pdf", ".png", ".jpg", ".jpeg"},
    "cashflow": {".xlsx", ".xls", ".csv", ".pdf", ".png", ".jpg", ".jpeg"},
    "statement": {".xlsx", ".xls", ".csv", ".pdf"},
    "tax": {".xlsx", ".xls", ".csv", ".pdf"},
    "plan": {".xlsx", ".docx", ".pdf"},
    "asset": {".pdf", ".png", ".jpg", ".jpeg"},
}


PRESETS: dict[str, dict[str, dict[str, Any]]] = {
    "M001": {
        "license": {
            "completeness_score": 100,
            "subject_match": True,
            "metrics": [("主体状态", "存续", "POSITIVE"), ("证照有效期", "长期", "POSITIVE")],
            "findings": ["统一社会信用代码与申请信息一致", "经营主体与法人核验结果一致"],
        },
        "cashflow": {
            "completeness_score": 98,
            "period_months": 12,
            "subject_match": True,
            "metrics": [("月均经营流入", "¥95,667", "POSITIVE"), ("流水完整度", "98%", "POSITIVE"), ("明显异常", "0 笔", "POSITIVE")],
            "findings": ["识别到连续 12 个月经营流水", "收款趋势稳定且主体一致"],
        },
        "statement": {
            "completeness_score": 96,
            "subject_match": True,
            "metrics": [("资产负债率", "34.2%", "POSITIVE"), ("流动比率", "1.86", "POSITIVE")],
            "findings": ["最近一期资产负债资料字段完整", "短期偿债覆盖处于样例安全区间"],
        },
        "tax": {
            "completeness_score": 97,
            "period_months": 12,
            "subject_match": True,
            "metrics": [("开票覆盖率", "95.1%", "POSITIVE"), ("连续申报", "12 个月", "POSITIVE")],
            "findings": ["开票收入与经营流水基本匹配", "样例期间未发现断档申报"],
        },
        "plan": {
            "completeness_score": 95,
            "period_months": 3,
            "subject_match": True,
            "metrics": [("计划资本开支", "¥20,000", "NEUTRAL"), ("未来偿债支出", "¥8,000", "NEUTRAL")],
            "findings": ["未来三个月资金用途清晰", "计划支出已纳入资金缺口压力测试"],
        },
        "asset": {
            "completeness_score": 92,
            "subject_match": True,
            "metrics": [("剩余租期", "18 个月", "POSITIVE"), ("设备账面价值", "¥160,000", "NEUTRAL")],
            "findings": ["门店租赁关系与经营地址一致", "该材料仅作补充证据，不作为授信必备抵押物"],
        },
    },
    "M005": {
        "license": {
            "completeness_score": 94,
            "subject_match": True,
            "metrics": [("主体状态", "存续", "POSITIVE"), ("经营状态", "存在关注项", "WARNING")],
            "findings": ["统一社会信用代码与申请信息一致", "工商经营状态需结合其他材料复核"],
            "warnings": ["许可信息中存在待核实经营状态备注"],
        },
        "cashflow": {
            "completeness_score": 82,
            "period_months": 12,
            "subject_match": False,
            "metrics": [("月均经营流入", "¥87,417", "NEUTRAL"), ("疑似异常交易", "17 笔", "DANGER"), ("个人账户占比", "31%", "WARNING")],
            "findings": ["识别到连续 12 个月流水", "发现整数金额重复、夜间交易集中和快速进出"],
            "warnings": ["部分交易对手及收款账户与申请主体不一致"],
        },
        "statement": {
            "completeness_score": 78,
            "subject_match": False,
            "metrics": [("资产负债率", "68.4%", "WARNING"), ("流动比率", "0.91", "DANGER")],
            "findings": ["短期负债对流动资产形成压力", "部分账户主体需补充说明"],
            "warnings": ["报表主体与部分流水账户名称不一致"],
        },
        "tax": {
            "completeness_score": 74,
            "period_months": 10,
            "subject_match": True,
            "metrics": [("开票覆盖率", "62.3%", "WARNING"), ("连续申报", "10 / 12 个月", "WARNING")],
            "findings": ["开票收入低于经营流水", "存在两个月申报资料缺口"],
            "warnings": ["建议补充缺失月份申报记录及未开票收入说明"],
        },
        "plan": {
            "completeness_score": 80,
            "period_months": 3,
            "subject_match": True,
            "metrics": [("计划资本开支", "¥150,000", "WARNING"), ("未来偿债支出", "¥45,000", "WARNING")],
            "findings": ["扩店投入与偿债支出同期发生", "计划支出将放大 P90 资金缺口"],
            "warnings": ["建议补充订单回款安排和备用资金来源"],
        },
        "asset": {
            "completeness_score": 68,
            "subject_match": True,
            "metrics": [("剩余租期", "4 个月", "WARNING"), ("设备证明", "部分缺失", "WARNING")],
            "findings": ["经营场所剩余租期较短", "该材料仅作补充证据，不作为授信必备抵押物"],
            "warnings": ["建议补充续租意向或新经营场所安排"],
        },
    },
}


def _decode_and_validate(request: MaterialParseRequest) -> bytes:
    extension = Path(request.file_name).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS[request.group]:
        allowed = "、".join(sorted(ALLOWED_EXTENSIONS[request.group]))
        raise ValueError(f"该材料不支持 {extension or '无扩展名'} 文件，可上传：{allowed}")
    try:
        content = base64.b64decode(request.content_base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("文件内容不是有效的 Base64 数据") from exc
    if len(content) != request.size_bytes:
        raise ValueError("文件大小与上传元数据不一致")
    if extension == ".pdf" and not content.startswith(b"%PDF"):
        raise ValueError("文件扩展名为 PDF，但内容签名不正确")
    if extension in {".xlsx", ".docx"} and not content.startswith(b"PK"):
        raise ValueError("Office 文件内容签名不正确")
    if extension in {".png"} and not content.startswith(b"\x89PNG"):
        raise ValueError("PNG 文件内容签名不正确")
    if extension in {".jpg", ".jpeg"} and not content.startswith(b"\xff\xd8"):
        raise ValueError("JPEG 文件内容签名不正确")
    return content


def parse_material(request: MaterialParseRequest) -> MaterialEvidence:
    content = _decode_and_validate(request)
    digest = hashlib.sha256(content).hexdigest()
    preset = PRESETS.get(request.merchant_id, {}).get(request.group, {})
    extraction = read_document(content, request.file_name)
    warnings = list(preset.get("warnings", []))
    warnings.extend(extraction.warnings)
    if request.merchant_id not in PRESETS:
        return _real_extraction_evidence(request, digest, extraction, warnings)
    return MaterialEvidence(
        material_id=f"MAT-{request.merchant_id}-{request.group.upper()}-{digest[:8]}",
        merchant_id=request.merchant_id,
        group=request.group,
        file_name=Path(request.file_name).name,
        media_type=request.media_type,
        size_bytes=request.size_bytes,
        sha256=digest,
        completeness_score=preset.get("completeness_score", 70),
        period_months=preset.get("period_months"),
        subject_match=preset.get("subject_match", True),
        extracted_metrics=[
            {"label": label, "value": value, "tone": tone}
            for label, value, tone in preset.get(
                "metrics", [("文件校验", "已通过", "NEUTRAL")]
            )
        ],
        findings=preset.get("findings", ["文件格式、大小与内容签名已通过校验"]),
        warnings=warnings,
    )


def _real_extraction_evidence(
    request: MaterialParseRequest,
    digest: str,
    extraction: DocumentExtraction,
    warnings: list[str],
) -> MaterialEvidence:
    metrics: list[dict[str, str]] = [
        {"label": "读取类型", "value": extraction.document_type, "tone": "NEUTRAL"},
        {
            "label": "可读取字符",
            "value": str(extraction.extracted_characters),
            "tone": "POSITIVE" if extraction.has_content else "WARNING",
        },
    ]
    if extraction.page_count:
        metrics.append({"label": "页数", "value": str(extraction.page_count), "tone": "NEUTRAL"})
    elif extraction.sheet_count:
        metrics.append({"label": "工作表", "value": str(extraction.sheet_count), "tone": "NEUTRAL"})
    elif extraction.row_count:
        metrics.append({"label": "有效行数", "value": str(extraction.row_count), "tone": "NEUTRAL"})

    findings = [
        f"已真实读取 {extraction.document_type} 文件并生成受限结构化摘要",
        "原始文件全文未写入日志，也未直接发送给大模型供应商",
    ]
    if extraction.numeric_cells:
        findings.append(f"检测到 {extraction.numeric_cells} 个数值单元格")
    warnings.append("尚未自动核验文件中的经营主体与申请主体是否一致")
    completeness = 85 if extraction.has_content else 45
    return MaterialEvidence(
        material_id=f"MAT-{request.merchant_id}-{request.group.upper()}-{digest[:8]}",
        merchant_id=request.merchant_id,
        group=request.group,
        file_name=Path(request.file_name).name,
        media_type=request.media_type,
        size_bytes=request.size_bytes,
        sha256=digest,
        simulated=False,
        completeness_score=completeness,
        period_months=extraction.period_months,
        subject_match=False,
        extracted_metrics=metrics[:3],
        findings=findings,
        warnings=warnings,
    )

