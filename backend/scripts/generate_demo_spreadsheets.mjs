import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const repoRoot = path.resolve(import.meta.dirname, "../..");
const outputRoot = path.join(repoRoot, "outputs", "material_upload_demo");
const previewRoot = path.join(repoRoot, "tmp", "material_builder", "previews");

const COLORS = {
  red: "#A71930",
  redSoft: "#F8E9ED",
  ink: "#262321",
  muted: "#6F6862",
  line: "#DED8D1",
  green: "#1F785F",
  greenSoft: "#E7F3EE",
  warning: "#A85C00",
  warningSoft: "#FFF1DB",
};

const cases = {
  M001: {
    merchantName: "宜人美发生活馆",
    socialCode: "91310000MA1DEMO001",
    address: "上海市示范区惠民路 88 号",
    openingCash: 118000,
    inflows: [82000, 85000, 89000, 93000, 95000, 97000, 99000, 101000, 103000, 105000, 99000, 100000],
    refunds: [1200, 900, 1100, 1000, 800, 900, 1100, 1000, 1200, 900, 800, 1000],
    outflows: [61000, 63000, 66000, 68000, 69000, 70000, 72000, 73000, 74000, 76000, 72000, 73500],
    invoices: [79000, 82000, 85000, 90000, 91000, 94000, 96000, 98000, 99000, 101000, 96000, 91000],
    taxes: [2450, 2580, 2680, 2790, 2870, 2950, 3020, 3100, 3180, 3260, 3090, 2980],
    filing: Array(12).fill("已申报"),
  },
  M005: {
    merchantName: "欣悦美发工作室",
    socialCode: "91310000MA1DEMO005",
    address: "上海市示范区惠民路 188 号",
    openingCash: 42000,
    inflows: [82000, 84000, 86000, 85000, 88000, 90000, 92000, 93000, 95000, 87000, 85000, 82000],
    refunds: [4200, 4900, 5100, 4600, 7200, 8500, 9100, 8200, 10500, 9800, 9300, 8700],
    outflows: [69000, 71000, 72000, 73000, 75000, 78000, 80000, 82000, 90000, 86000, 84000, 81000],
    invoices: [52000, 56000, 0, 59000, 60000, 63000, 65000, 0, 67000, 54000, 52000, 51000],
    taxes: [1650, 1720, 0, 1810, 1850, 1920, 1980, 0, 2050, 1690, 1610, 1580],
    filing: ["已申报", "已申报", "缺失", "已申报", "已申报", "已申报", "已申报", "缺失", "已申报", "已申报", "已申报", "已申报"],
  },
};

const months = [
  "2025-08", "2025-09", "2025-10", "2025-11", "2025-12", "2026-01",
  "2026-02", "2026-03", "2026-04", "2026-05", "2026-06", "2026-07",
];

function styleTitle(sheet, title, subtitle) {
  sheet.showGridLines = false;
  sheet.getRange("A1:F1").merge();
  sheet.getRange("A1").values = [[title]];
  sheet.getRange("A1:F1").format = {
    fill: COLORS.red,
    font: { bold: true, color: "#FFFFFF", size: 18 },
    verticalAlignment: "center",
  };
  sheet.getRange("A1:F1").format.rowHeight = 36;
  sheet.getRange("A2:F2").merge();
  sheet.getRange("A2").values = [[subtitle]];
  sheet.getRange("A2:F2").format = {
    fill: COLORS.redSoft,
    font: { color: COLORS.red, italic: true, size: 10 },
    verticalAlignment: "center",
  };
  sheet.getRange("A2:F2").format.rowHeight = 24;
}

function styleMetadata(sheet) {
  sheet.getRange("A4:F6").format = {
    fill: "#F7F5F2",
    font: { color: COLORS.ink, size: 10 },
    borders: { preset: "outside", style: "thin", color: COLORS.line },
  };
  sheet.getRange("A4:A6").format.font = { bold: true, color: COLORS.muted };
  sheet.getRange("C4:C6").format.font = { bold: true, color: COLORS.muted };
  sheet.getRange("E4:E6").format.font = { bold: true, color: COLORS.muted };
}

function styleTable(sheet, range) {
  sheet.getRange(range).format = {
    font: { color: COLORS.ink, size: 10 },
    borders: {
      insideHorizontal: { style: "thin", color: COLORS.line },
      bottom: { style: "thin", color: COLORS.line },
    },
  };
}

async function buildCashflow(merchantId, data) {
  const workbook = Workbook.create();
  const sheet = workbook.worksheets.add("经营流水");
  styleTitle(sheet, `${merchantId} 近 12 个月经营流水`, "工行杯竞赛模拟材料 - 数据仅用于产品演示，不代表真实银行流水");
  sheet.getRange("A4:F6").values = [
    ["经营主体", data.merchantName, "统一社会信用代码", data.socialCode, "币种", "人民币"],
    ["经营地址", data.address, "统计周期", "2025-08 至 2026-07", "期初余额", data.openingCash],
    ["数据来源", "模拟对公及平台收款", "主体校验", merchantId === "M001" ? "一致" : "存在个人账户收款", "材料版本", "DEMO-2026.08"],
  ];
  styleMetadata(sheet);
  sheet.getRange("F5").format.numberFormat = "¥#,##0;[Red](¥#,##0);-";

  sheet.getRange("A8:F8").values = [["月份", "经营流入", "退款/冲正", "经营支出", "净现金流", "期末余额"]];
  sheet.getRange("A8:F8").format = {
    fill: COLORS.ink,
    font: { bold: true, color: "#FFFFFF", size: 10 },
    horizontalAlignment: "center",
  };
  const rows = months.map((month, index) => [month, data.inflows[index], data.refunds[index], data.outflows[index], null, null]);
  sheet.getRange("A9:F20").values = rows;
  sheet.getRange("E9").formulas = [["=B9-C9-D9"]];
  sheet.getRange("E9:E20").fillDown();
  sheet.getRange("F9").formulas = [["=$F$5+E9"]];
  sheet.getRange("F10").formulas = [["=F9+E10"]];
  sheet.getRange("F10:F20").fillDown();
  styleTable(sheet, "A9:F20");
  sheet.getRange("B9:F20").format.numberFormat = "¥#,##0;[Red](¥#,##0);-";
  sheet.getRange("A9:A20").format.horizontalAlignment = "center";

  sheet.getRange("A22:F22").values = [["合计 / 均值", null, null, null, null, null]];
  sheet.getRange("B22").formulas = [["=SUM(B9:B20)"]];
  sheet.getRange("C22").formulas = [["=SUM(C9:C20)"]];
  sheet.getRange("D22").formulas = [["=SUM(D9:D20)"]];
  sheet.getRange("E22").formulas = [["=SUM(E9:E20)"]];
  sheet.getRange("F22").formulas = [["=F20"]];
  sheet.getRange("A22:F22").format = {
    fill: COLORS.redSoft,
    font: { bold: true, color: COLORS.red },
    borders: { top: { style: "double", color: COLORS.red } },
  };
  sheet.getRange("B22:F22").format.numberFormat = "¥#,##0;[Red](¥#,##0);-";

  sheet.getRange("A24:F25").merge(true);
  sheet.getRange("A24").values = [[merchantId === "M001" ? "解析提示：连续 12 个月数据完整，未发现明显异常。" : "解析提示：存在整数金额重复、退款偏高及主体账户不一致，请进入人工复核。"]];
  sheet.getRange("A25").values = [["隐私提示：本文件为完全虚构的竞赛模拟材料，不包含真实个人或企业金融信息。"]];
  sheet.getRange("A24:F25").format = {
    fill: merchantId === "M001" ? COLORS.greenSoft : COLORS.warningSoft,
    font: { color: merchantId === "M001" ? COLORS.green : COLORS.warning, size: 10 },
    wrapText: true,
  };

  sheet.freezePanes.freezeRows(8);
  sheet.getRange("A1:F25").format.autofitRows();
  sheet.getRange("A:A").format.columnWidth = 13;
  sheet.getRange("B:B").format.columnWidth = 25;
  sheet.getRange("C:C").format.columnWidth = 18;
  sheet.getRange("D:D").format.columnWidth = 23;
  sheet.getRange("E:E").format.columnWidth = 14;
  sheet.getRange("F:F").format.columnWidth = 17;

  return { workbook, sheetName: "经营流水" };
}

async function buildTax(merchantId, data) {
  const workbook = Workbook.create();
  const sheet = workbook.worksheets.add("纳税开票汇总");
  styleTitle(sheet, `${merchantId} 纳税与开票汇总`, "工行杯竞赛模拟材料 - 用于经营真实性与流水交叉验证");
  sheet.getRange("A4:F6").values = [
    ["经营主体", data.merchantName, "统一社会信用代码", data.socialCode, "币种", "人民币"],
    ["统计周期", "2025-08 至 2026-07", "申报口径", "月度模拟申报", "材料版本", "DEMO-2026.08"],
    ["开票主体", data.merchantName, "主体校验", "一致", "数据性质", "竞赛模拟"],
  ];
  styleMetadata(sheet);

  sheet.getRange("A8:F8").values = [["月份", "经营收款", "开票收入", "开票覆盖率", "模拟税额", "申报状态"]];
  sheet.getRange("A8:F8").format = {
    fill: COLORS.ink,
    font: { bold: true, color: "#FFFFFF", size: 10 },
    horizontalAlignment: "center",
  };
  sheet.getRange("A9:F20").values = months.map((month, index) => [month, data.inflows[index], data.invoices[index], null, data.taxes[index], data.filing[index]]);
  sheet.getRange("D9").formulas = [["=IFERROR(C9/B9,0)"]];
  sheet.getRange("D9:D20").fillDown();
  styleTable(sheet, "A9:F20");
  sheet.getRange("B9:C20").format.numberFormat = "¥#,##0;[Red](¥#,##0);-";
  sheet.getRange("D9:D20").format.numberFormat = "0.0%";
  sheet.getRange("E9:E20").format.numberFormat = "¥#,##0;[Red](¥#,##0);-";
  sheet.getRange("A9:A20").format.horizontalAlignment = "center";
  sheet.getRange("F9:F20").conditionalFormats.addCustom('=F9="缺失"', {
    fill: COLORS.warningSoft,
    font: { bold: true, color: COLORS.warning },
  });

  sheet.getRange("A22:F22").values = [["汇总", null, null, null, null, null]];
  sheet.getRange("B22").formulas = [["=SUM(B9:B20)"]];
  sheet.getRange("C22").formulas = [["=SUM(C9:C20)"]];
  sheet.getRange("D22").formulas = [["=IFERROR(C22/B22,0)"]];
  sheet.getRange("E22").formulas = [["=SUM(E9:E20)"]];
  sheet.getRange("F22").formulas = [["=COUNTIF(F9:F20,\"已申报\")&\" / 12 个月\""]];
  sheet.getRange("A22:F22").format = {
    fill: COLORS.redSoft,
    font: { bold: true, color: COLORS.red },
    borders: { top: { style: "double", color: COLORS.red } },
  };
  sheet.getRange("B22:C22").format.numberFormat = "¥#,##0;[Red](¥#,##0);-";
  sheet.getRange("D22").format.numberFormat = "0.0%";
  sheet.getRange("E22").format.numberFormat = "¥#,##0;[Red](¥#,##0);-";

  sheet.getRange("A24:F25").merge(true);
  sheet.getRange("A24").values = [[merchantId === "M001" ? "解析提示：开票与经营收款基本匹配，申报资料连续。" : "解析提示：开票覆盖率偏低且存在两个月资料缺口，建议补件。"]];
  sheet.getRange("A25").values = [["隐私提示：本文件为完全虚构的竞赛模拟材料，不构成真实纳税申报或完税证明。"]];
  sheet.getRange("A24:F25").format = {
    fill: merchantId === "M001" ? COLORS.greenSoft : COLORS.warningSoft,
    font: { color: merchantId === "M001" ? COLORS.green : COLORS.warning, size: 10 },
    wrapText: true,
  };

  sheet.freezePanes.freezeRows(8);
  sheet.getRange("A1:F25").format.autofitRows();
  sheet.getRange("A:A").format.columnWidth = 13;
  sheet.getRange("B:B").format.columnWidth = 25;
  sheet.getRange("C:C").format.columnWidth = 18;
  sheet.getRange("D:D").format.columnWidth = 23;
  sheet.getRange("E:E").format.columnWidth = 14;
  sheet.getRange("F:F").format.columnWidth = 17;
  return { workbook, sheetName: "纳税开票汇总" };
}

async function saveWorkbook(merchantId, type, built) {
  const targetDir = path.join(outputRoot, merchantId);
  await fs.mkdir(targetDir, { recursive: true });
  await fs.mkdir(previewRoot, { recursive: true });
  const filename = type === "cashflow" ? `${merchantId}_cashflow_12m.xlsx` : `${merchantId}_tax_invoice_12m.xlsx`;
  const xlsx = await SpreadsheetFile.exportXlsx(built.workbook);
  await xlsx.save(path.join(targetDir, filename));

  const inspect = await built.workbook.inspect({
    kind: "table",
    range: `${built.sheetName}!A1:F25`,
    include: "values,formulas",
    tableMaxRows: 25,
    tableMaxCols: 6,
  });
  console.log(`${merchantId} ${type} inspect\n${inspect.ndjson}`);
  const errors = await built.workbook.inspect({
    kind: "match",
    searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
    options: { useRegex: true, maxResults: 100 },
    summary: `${merchantId} ${type} formula error scan`,
  });
  console.log(errors.ndjson);
  const preview = await built.workbook.render({
    sheetName: built.sheetName,
    range: "A1:F25",
    scale: 1.5,
    format: "png",
  });
  await fs.writeFile(
    path.join(previewRoot, `${merchantId}_${type}.png`),
    new Uint8Array(await preview.arrayBuffer()),
  );
}

await fs.mkdir(outputRoot, { recursive: true });
for (const [merchantId, data] of Object.entries(cases)) {
  await saveWorkbook(merchantId, "cashflow", await buildCashflow(merchantId, data));
  await saveWorkbook(merchantId, "tax", await buildTax(merchantId, data));
}

console.log(`Generated demo workbooks in ${outputRoot}`);
