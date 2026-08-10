export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'MANUAL_REVIEW'
export type Confidence = 'LOW' | 'MEDIUM' | 'HIGH'
export type ModuleState = 'READY' | 'NOT_PROVIDED'

export interface ReviewRule {
  code: string
  level: 'HIGH' | 'MEDIUM'
  message: string
}

export interface DimensionScores {
  stability: number
  growth: number
  authenticity: number
  capacity: number
  online_reputation: number
  social_activity: number
  complaint_risk: number
  unstructured: number
}

export interface ScoreResult {
  merchant_id: string
  merchant_name: string
  profile: string
  score_version: string
  dimensions: DimensionScores
  operating_credit_score: number
  credit_grade: 'A' | 'B' | 'C' | 'D' | 'E'
  risk_band: RiskLevel
  pd_12m: null
  pd_status: 'UNCALIBRATED'
  confidence: Confidence
  decision: 'APPROVE' | 'MANUAL_REVIEW' | 'DECLINE'
  review_required: boolean
  review_rules: ReviewRule[]
  positive_reasons: string[]
  negative_reasons: string[]
  limit: {
    score_multiplier: number | null
    stability_factor: number
    capacity_factor: number
    growth_bonus: number
    recommended_limit: number
  }
}

export interface AnomalyRule {
  code: string
  level: 'HIGH' | 'MEDIUM'
  contribution: number
  message: string
  evidence_transaction_ids: string[]
}

export interface AnomalyResult {
  merchant_id: string
  evaluated_at: string
  transaction_count: number
  recent_transaction_count: number
  anomaly_score: number
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH'
  confidence: Confidence
  reason_codes: string[]
  rule_hits: AnomalyRule[]
  evidence_transaction_ids: string[]
  model_version: string
}

export interface CashForecast {
  forecast_month: string
  p50_operating_inflow: number
  p50_operating_outflow: number
  p50_ending_cash: number
  p50_funding_gap: number
  p90_operating_inflow: number
  p90_operating_outflow: number
  p90_ending_cash: number
  p90_funding_gap: number
  planned_capex: number
  debt_service: number
}

export interface CashGapResult {
  merchant_id: string
  snapshot_date: string
  horizon_months: number
  available_cash_at_snapshot: number
  minimum_cash_balance: number
  unused_credit: number
  forecasts: CashForecast[]
  max_p50_funding_gap: number
  max_p90_funding_gap: number
  first_p50_gap_month: string | null
  first_p90_gap_month: string | null
  p90_need_after_unused_credit: number
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH'
  confidence: 'MEDIUM' | 'HIGH'
  drivers: string[]
  model_version: string
}

export interface FullAnalysisResult {
  merchant_id: string
  generated_at: string
  overall_risk: RiskLevel
  module_states: {
    score: 'READY'
    anomaly: ModuleState
    cash_gap: ModuleState
  }
  data_warnings: string[]
  score: ScoreResult
  anomaly: AnomalyResult | null
  cash_gap: CashGapResult | null
  api_version: string
}

export interface ApplicationDraft {
  merchantName: string
  industry: string
  socialCreditCode: string
  address: string
  legalName: string
  contactPhone: string
  requestedAmount: number
}

export type DemoCase = 'normal' | 'review'
export type DataSource = 'api' | 'mock'
