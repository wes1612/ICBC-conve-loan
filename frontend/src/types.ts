export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'MANUAL_REVIEW'
export type Confidence = 'LOW' | 'MEDIUM' | 'HIGH'
export type ModuleState = 'READY' | 'NOT_PROVIDED'
export type OverallDecision = 'APPROVE' | 'MANUAL_REVIEW' | 'DECLINE'
export type AnalysisMode = 'api' | 'mock'
export type PortalMode = 'merchant' | 'reviewer'
export type DataGroupId = 'cashflow' | 'statement' | 'tax' | 'plan'
export type MaterialGroupId = 'license' | DataGroupId | 'asset'
export type MetricTone = 'NEUTRAL' | 'POSITIVE' | 'WARNING' | 'DANGER'
export type UseOfFunds = '设备采购' | '装修扩店' | '旺季备货' | '人员扩充' | '平台活动垫资' | '租金工资周转' | '其他经营周转'
export type RepaymentSource = '经营现金流' | '平台订单回款' | '工行账户自动扣款' | '其他经营收入'

export type ConnectorId =
  | 'bank'
  | 'unionpay'
  | 'alipay'
  | 'wechat'
  | 'meituan'
  | 'douyin'
  | 'xiaohongshu'
  | 'enterprise'

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

export interface EligibilityResult {
  status: 'ELIGIBLE' | 'SUPPLEMENT_REQUIRED' | 'OUT_OF_SCOPE' | 'MANUAL_REVIEW'
  conclusion: string
  pilot_industry: boolean
  reasons: string[]
  warnings: string[]
}

export interface LoanTerms {
  requested_amount: number
  recommended_limit: number
  limit_range: [number, number]
  tenor_months: number
  repayment_method: string
  is_revolving: boolean
  drawdown_rule: string
  renewal_rule: string
  limit_adjustment_rule: string
  use_of_funds: UseOfFunds
  use_of_funds_match: string
  use_of_funds_warnings: string[]
  expected_repayment_source: RepaymentSource
  repayment_source_note: string
}

export interface RepaymentCapacity {
  conclusion: string
  confidence: Confidence
  monthly_operating_inflow: number | null
  monthly_operating_outflow: number | null
  fixed_cost_coverage: number | null
  p90_funding_gap: number | null
  debt_pressure_level: string
  refund_complaint_pressure: string
  evidence: string[]
}

export interface AuditTrail {
  consent_version: string
  consent_timestamp: string | null
  authorized_sources: ConnectorId[]
  material_hashes: Record<string, string>
  material_ids: string[]
  score_version: string
  rules_version: string
  model_version: string
  generated_at: string
  ai_used: boolean
}


export interface PolicyRecommendation {
  policy_id: string
  policy_name: string
  policy_type: string
  policy_level: string
  support_method: string
  support_standard: string
  match_level: 'HIGH' | 'MEDIUM' | 'LOW' | 'CANDIDATE'
  reason: string
  required_materials: string[]
  application_steps: string[]
  bank_actions: string[]
  consumer_introduction: string[]
  source_url: string | null
  application_deadline: string | null
  status: 'ACTIVE' | 'DRAFT' | 'EXPIRED'
  warnings: string[]
}
export interface FullAnalysisResult {
  merchant_id: string
  generated_at: string
  overall_risk: RiskLevel
  overall_decision: OverallDecision
  module_states: {
    score: 'READY'
    anomaly: ModuleState
    cash_gap: ModuleState
  }
  data_warnings: string[]
  score: ScoreResult
  anomaly: AnomalyResult | null
  cash_gap: CashGapResult | null
  material_evidence: MaterialEvidence[]
  eligibility: EligibilityResult
  loan_terms: LoanTerms
  repayment_capacity: RepaymentCapacity
  audit_trail: AuditTrail
  policy_recommendations: PolicyRecommendation[]
  api_version: string
}

export interface ExtractedMetric {
  label: string
  value: string
  tone: MetricTone
}

export interface MaterialEvidence {
  material_id: string
  merchant_id: string
  group: MaterialGroupId
  file_name: string
  media_type: string
  size_bytes: number
  sha256: string
  parse_status: 'PARSED'
  simulated: boolean
  completeness_score: number
  period_months: number | null
  subject_match: boolean
  extracted_metrics: ExtractedMetric[]
  findings: string[]
  warnings: string[]
}

export interface ApplicationDraft {
  merchantName: string
  industry: string
  socialCreditCode: string
  province: string
  city: string
  address: string
  legalName: string
  legalPhone: string
  legalIdNumber: string
  contactName: string
  contactPhone: string
  contactIdNumber: string
  requestedAmount: number
  useOfFunds: UseOfFunds
  requestedTenorMonths: number
  expectedRepaymentSource: RepaymentSource
}

export interface ApplicationContext {
  social_credit_code: string
  province: string
  city: string
  operating_address: string
  legal_name: string
  legal_phone: string
  legal_id_number: string | null
  contact_name: string
  contact_phone: string
  contact_id_number: string | null
  industry: string
  requested_amount: number
  use_of_funds: UseOfFunds
  requested_tenor_months: number
  expected_repayment_source: RepaymentSource
  identity_verified: boolean
  uploaded_data_groups: DataGroupId[]
  authorized_sources: ConnectorId[]
  consent_confirmed: boolean
  consent_version: string
  consented_at: string | null
  materials: MaterialEvidence[]
}

export interface FullAnalysisRequest {
  application: ApplicationContext
  merchant: Record<string, unknown>
  anomaly?: Record<string, unknown> | null
  cash_gap?: Record<string, unknown> | null
}

export type DemoCase = 'normal' | 'review'
export type DataSource = 'api' | 'mock'

export type WorkflowStep = 'identity' | 'verify' | 'data' | 'authorize' | 'results'

export interface AssistantHistoryMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface AssistantMaterialStatus {
  material_id: string
  group: MaterialGroupId
  completeness_score: number
  subject_match: boolean
  warnings: string[]
}

export interface AssistantWorkflowContext {
  merchant_id: string | null
  identity_verified: boolean
  materials: AssistantMaterialStatus[]
  authorized_sources: ConnectorId[]
  consent_confirmed: boolean
  analysis: FullAnalysisResult | null
}

export interface AssistantMessageRequest {
  message: string
  current_step: WorkflowStep
  context: AssistantWorkflowContext
  history: AssistantHistoryMessage[]
}

export interface AssistantReply {
  answer: string
  evidence_refs: string[]
  should_escalate: boolean
}

export interface AiReportSummary {
  overall_summary: string
  positive_factors: string[]
  risk_factors: string[]
  cash_gap_interpretation: string
  recommended_actions: string[]
  evidence_refs: string[]
  disclaimer: 'AI仅解释既有分析结果，不参与评分与授信决策。'
}
