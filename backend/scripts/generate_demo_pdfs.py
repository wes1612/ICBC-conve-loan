"""生成 M001/M005 竞赛演示材料 PDF。"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOT = REPO_ROOT / "output" / "pdf" / "demo_materials"
RED = colors.HexColor("#A71930")
RED_SOFT = colors.HexColor("#F8E9ED")
INK = colors.HexColor("#262321")
MUTED = colors.HexColor("#6F6862")
LINE = colors.HexColor("#DED8D1")
PAPER = colors.HexColor("#F7F5F2")
GREEN = colors.HexColor("#1F785F")
WARNING = colors.HexColor("#A85C00")

pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))

styles = getSampleStyleSheet()
TITLE = ParagraphStyle("ChineseTitle", fontName="STSong-Light", fontSize=21, leading=27, textColor=INK, spaceAfter=5 * mm)
SUBTITLE = ParagraphStyle("ChineseSubtitle", fontName="STSong-Light", fontSize=9, leading=14, textColor=MUTED)
SECTION = ParagraphStyle("ChineseSection", fontName="STSong-Light", fontSize=12, leading=18, textColor=RED, spaceBefore=5 * mm, spaceAfter=2 * mm)
BODY = ParagraphStyle("ChineseBody", fontName="STSong-Light", fontSize=9.5, leading=15, textColor=INK)
SMALL = ParagraphStyle("ChineseSmall", fontName="STSong-Light", fontSize=8, leading=12, textColor=MUTED)
BADGE = ParagraphStyle("ChineseBadge", fontName="STSong-Light", fontSize=9, leading=13, textColor=colors.white, alignment=TA_CENTER)
TABLE_HEADER = ParagraphStyle("ChineseTableHeader", fontName="STSong-Light", fontSize=9, leading=13, textColor=colors.white, alignment=TA_LEFT)


CASES = {
    "M001": {
        "name": "宜人美发生活馆",
        "code": "91310000MA1DEMO001",
        "legal": "李女士",
        "address": "上海市示范区惠民路 88 号",
        "status": "存续",
        "established": "2021-05-18",
        "assets": "468,000",
        "liabilities": "160,000",
        "equity": "308,000",
        "current_assets": "335,000",
        "current_liabilities": "180,000",
        "debt_ratio": "34.2%",
        "current_ratio": "1.86",
        "plan_rows": [["2026-08", "设备维护", "8,000", "3,000"], ["2026-09", "门店升级", "12,000", "3,000"], ["2026-10", "常规经营", "0", "2,000"]],
        "plan_note": "未来三个月资金用途清晰，计划支出已纳入资金缺口压力测试。",
        "lease": "2025-02-01 至 2028-01-31",
        "remaining": "18 个月",
        "equipment": "160,000",
        "asset_note": "门店租赁关系与经营地址一致；仅作补充经营证据，不作为授信必备抵押物。",
        "tone": GREEN,
    },
    "M005": {
        "name": "欣悦美发工作室",
        "code": "91310000MA1DEMO005",
        "legal": "王女士",
        "address": "上海市示范区惠民路 188 号",
        "status": "存续 - 存在关注项",
        "established": "2024-12-06",
        "assets": "285,000",
        "liabilities": "195,000",
        "equity": "90,000",
        "current_assets": "146,000",
        "current_liabilities": "160,000",
        "debt_ratio": "68.4%",
        "current_ratio": "0.91",
        "plan_rows": [["2026-08", "扩店定金", "80,000", "15,000"], ["2026-09", "设备采购", "70,000", "15,000"], ["2026-10", "运营投放", "0", "15,000"]],
        "plan_note": "扩店投入与偿债支出同期发生，建议补充订单回款安排和备用资金来源。",
        "lease": "2025-01-01 至 2026-12-31",
        "remaining": "4 个月",
        "equipment": "证明不完整",
        "asset_note": "经营场所剩余租期较短，建议补充续租意向；该材料不作为必备抵押物。",
        "tone": WARNING,
    },
}


def para(text: str, style: ParagraphStyle = BODY) -> Paragraph:
    return Paragraph(text, style)


def table(data: list[list[str]], widths: list[float] | None = None, header: bool = False) -> Table:
    rows = [
        [
            para(
                str(value),
                TABLE_HEADER if header and row_index == 0 else SMALL if row_index else BODY,
            )
            for value in row
        ]
        for row_index, row in enumerate(data)
    ]
    result = Table(rows, colWidths=widths, hAlign="LEFT")
    commands = [
        ("FONTNAME", (0, 0), (-1, -1), "STSong-Light"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (-1, -1), INK),
        ("GRID", (0, 0), (-1, -1), 0.35, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]
    if header:
        commands.extend([
            ("BACKGROUND", (0, 0), (-1, 0), INK),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ])
    else:
        commands.extend([
            ("BACKGROUND", (0, 0), (0, -1), PAPER),
            ("BACKGROUND", (2, 0), (2, -1), PAPER),
        ])
    result.setStyle(TableStyle(commands))
    return result


def header(story: list, merchant_id: str, title: str, subtitle: str) -> None:
    badge = Table([[para("工行杯竞赛模拟材料", BADGE)]], colWidths=[42 * mm], rowHeights=[8 * mm])
    badge.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), RED), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    story.extend([badge, Spacer(1, 5 * mm), para(title, TITLE), para(f"材料编号：{merchant_id} - {subtitle}", SUBTITLE), Spacer(1, 4 * mm)])


def footer(story: list) -> None:
    story.extend([
        Spacer(1, 7 * mm),
        para("重要声明", SECTION),
        para("本文件中的主体、金额、日期和证明信息均为虚构的竞赛模拟数据，仅用于验证材料上传、解析和风险审核流程，不构成真实证照、财务报表、合同或产权证明。", SMALL),
    ])


def build_pdf(path: Path, title: str, merchant_id: str, story: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(path), pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=16 * mm, title=title,
        author="融策 - 工行杯竞赛项目",
    )
    document.build(story)


def build_license(merchant_id: str, data: dict) -> None:
    story: list = []
    header(story, merchant_id, "经营主体证明（模拟营业执照信息页）", "LICENSE")
    story.append(para("主体登记信息", SECTION))
    story.append(table([
        ["经营主体", data["name"], "统一社会信用代码", data["code"]],
        ["法定代表人", data["legal"], "登记状态", data["status"]],
        ["成立日期", data["established"], "营业期限", "长期"],
        ["经营地址", data["address"], "核验结果", "申请信息一致"],
    ], [30 * mm, 55 * mm, 35 * mm, 52 * mm]))
    story.append(para("模拟解析结论", SECTION))
    note = Table([[para("统一社会信用代码、主体名称及经营地址已完成交叉校验。", BODY)]], colWidths=[172 * mm])
    note.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), RED_SOFT), ("BOX", (0, 0), (-1, -1), 0.5, RED), ("LEFTPADDING", (0, 0), (-1, -1), 10), ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 9)]))
    story.append(note)
    footer(story)
    build_pdf(OUTPUT_ROOT / merchant_id / f"{merchant_id}_business_license.pdf", f"{merchant_id} 经营主体证明", merchant_id, story)


def build_statement(merchant_id: str, data: dict) -> None:
    story: list = []
    header(story, merchant_id, "最近一期经营资产负债摘要", "STATEMENT")
    story.append(para("报表概览（人民币元）", SECTION))
    story.append(table([
        ["资产总额", data["assets"], "负债总额", data["liabilities"]],
        ["所有者权益", data["equity"], "资产负债率", data["debt_ratio"]],
        ["流动资产", data["current_assets"], "流动负债", data["current_liabilities"]],
        ["流动比率", data["current_ratio"], "报表日期", "2026-07-31"],
    ], [32 * mm, 52 * mm, 32 * mm, 56 * mm]))
    story.append(para("模拟解析结论", SECTION))
    message = "资产结构稳定，短期偿债覆盖处于样例安全区间。" if merchant_id == "M001" else "资产负债率较高且流动比率低于 1，建议结合流水账户主体进行人工复核。"
    story.append(para(message, BODY))
    footer(story)
    build_pdf(OUTPUT_ROOT / merchant_id / f"{merchant_id}_financial_statement.pdf", f"{merchant_id} 资产负债摘要", merchant_id, story)


def build_plan(merchant_id: str, data: dict) -> None:
    story: list = []
    header(story, merchant_id, "未来三个月经营与资金使用计划", "PLAN")
    story.append(para("资金计划（人民币元）", SECTION))
    story.append(table([["月份", "主要用途", "计划资本开支", "还本付息"]] + data["plan_rows"], [32 * mm, 58 * mm, 40 * mm, 42 * mm], header=True))
    story.append(para("计划说明", SECTION))
    story.append(para(data["plan_note"], BODY))
    story.append(Spacer(1, 3 * mm))
    story.append(para("模型使用方式：资本开支和还本付息将进入未来三个月 P50/P90 资金缺口预测；未知支出不会按零处理。", SMALL))
    footer(story)
    build_pdf(OUTPUT_ROOT / merchant_id / f"{merchant_id}_business_plan.pdf", f"{merchant_id} 经营计划", merchant_id, story)


def build_asset(merchant_id: str, data: dict) -> None:
    story: list = []
    header(story, merchant_id, "经营场所租赁与设备证明摘要", "ASSET-OPTIONAL")
    story.append(para("补充经营证据", SECTION))
    story.append(table([
        ["经营地址", data["address"], "租赁期限", data["lease"]],
        ["剩余租期", data["remaining"], "设备账面价值", data["equipment"]],
        ["材料属性", "可选补充", "是否作为抵押要求", "否"],
    ], [30 * mm, 54 * mm, 38 * mm, 50 * mm]))
    story.append(para("模拟解析结论", SECTION))
    story.append(para(data["asset_note"], BODY))
    footer(story)
    build_pdf(OUTPUT_ROOT / merchant_id / f"{merchant_id}_lease_asset_proof.pdf", f"{merchant_id} 租赁与设备证明", merchant_id, story)


def main() -> None:
    for merchant_id, data in CASES.items():
        build_license(merchant_id, data)
        build_statement(merchant_id, data)
        build_plan(merchant_id, data)
        build_asset(merchant_id, data)
    print(f"Generated demo PDFs in {OUTPUT_ROOT}")


if __name__ == "__main__":
    main()
