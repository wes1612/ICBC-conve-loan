PRAGMA foreign_keys = ON;

CREATE TABLE merchants (
    merchant_id TEXT PRIMARY KEY,
    merchant_no INTEGER NOT NULL UNIQUE,
    merchant_name TEXT NOT NULL,
    industry TEXT,
    profile_type TEXT,
    test_purpose TEXT
);

CREATE TABLE merchant_basic_facts (
    fact_id INTEGER PRIMARY KEY AUTOINCREMENT,
    merchant_id TEXT NOT NULL REFERENCES merchants(merchant_id) ON DELETE CASCADE,
    field_name TEXT NOT NULL,
    value_text TEXT,
    value_number REAL,
    source_section TEXT NOT NULL DEFAULT '基础信息',
    UNIQUE (merchant_id, field_name)
);

CREATE TABLE merchant_financial_snapshots (
    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    merchant_id TEXT NOT NULL REFERENCES merchants(merchant_id) ON DELETE CASCADE,
    operating_cash_inflow_6m REAL,
    operating_cash_outflow_6m REAL,
    total_assets REAL,
    total_liabilities REAL,
    current_assets REAL,
    current_liabilities REAL,
    balance_sheet_provided TEXT,
    taxpayer_id TEXT,
    taxpayer_name TEXT,
    tax_period TEXT,
    tax_operating_income REAL,
    tax_operating_cost REAL,
    tax_total_profit REAL,
    tax_actual_profit REAL,
    tax_rate REAL,
    tax_payable REAL,
    tax_prepaid REAL,
    tax_current_due REAL,
    tax_revenue_invoice_gap_rate REAL,
    tax_compliance_bool INTEGER,
    tax_compliance_reason TEXT
);

CREATE TABLE merchant_invoice_validations (
    validation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    merchant_id TEXT NOT NULL REFERENCES merchants(merchant_id) ON DELETE CASCADE,
    sales_invoice_amount_12m REAL,
    purchase_expense_invoice_amount_12m REAL,
    invoice_count_total INTEGER,
    invoice_count_valid INTEGER,
    cashflow_abnormal_pattern_hits INTEGER,
    contract_invoice_match_result TEXT,
    extra_inconsistency_count INTEGER
);

CREATE TABLE merchant_monthly_series (
    series_id INTEGER PRIMARY KEY AUTOINCREMENT,
    merchant_id TEXT NOT NULL REFERENCES merchants(merchant_id) ON DELETE CASCADE,
    month TEXT NOT NULL,
    monthly_receipts REAL,
    platform_orders INTEGER,
    platform_redemption_rate REAL,
    platform_refund_rate REAL,
    UNIQUE (merchant_id, month)
);

CREATE VIEW v_structural_tax_summary AS
SELECT
    m.merchant_id,
    m.merchant_name,
    fs.tax_operating_income,
    fs.tax_payable,
    fs.tax_prepaid,
    fs.tax_current_due,
    fs.tax_revenue_invoice_gap_rate,
    fs.tax_compliance_bool,
    fs.tax_compliance_reason
FROM merchants AS m
JOIN merchant_financial_snapshots AS fs ON fs.merchant_id = m.merchant_id;
