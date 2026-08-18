export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'MANUAL_REVIEW'
export type Confidence = 'LOW' | 'MEDIUM' | 'HIGH'
export type ModuleState = 'READY' | 'NOT_PROVIDED'
export type OverallDecision = 'APPROVE' | 'MANUAL_REVIEW' | 'DECLINE'
export type AnalysisMode = 'api' | 'mock'
export type PortalMode = 'merchant' | 'reviewer'
export type DataGroupId = 'cashflow' | 'statement' | 'tax' | 'plan'
export type MaterialGroupId = 'license' | DataGroupId | 'asset'
export type MetricTone = 'NEUTRAL' | 'POSITIVE' | 'WARNING' | 'DANGER'
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
  identity_verified: boolean
  uploaded_data_groups: DataGroupId[]
  authorized_sources: ConnectorId[]
  consent_confirmed: boolean
  consented_at: string | null
  materials: MaterialEvidence[]
}

export interface FullAnalysisRequest {
  application: ApplicationContext
  merchant: Record<string, unknown>
  anomaly?: Record<string, unknown> | null
  cash_gap?: Record<string, unknown> | null
}

export type DemoMerchantId = 'M001' | 'M002' | 'M003' | 'M004' | 'M005'

export interface DemoApplicant {
  merchant_name: string
  industry: string
  social_credit_code: string
  province: string
  city: string
  address: string
  legal_name: string
  legal_phone: string
  legal_id_number: string
  contact_name: string
  contact_phone: string
  contact_id_number: string
  requested_amount: number
}

export interface DemoCasePayload {
  merchant_id: DemoMerchantId
  case_label: string
  case_description: string
  expected_risk: RiskLevel
  expected_decision: OverallDecision
  applicant: DemoApplicant
  merchant: Record<string, unknown>
  anomaly: Record<string, unknown>
  cash_gap: Record<string, unknown>
  materials: MaterialEvidence[]
}

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

export type PostLoanAction = 'INCREASE' | 'MAINTAIN' | 'DECREASE' | 'FREEZE' | 'MANUAL_REVIEW'
export type PostLoanAlertLevel = 'LOW' | 'MEDIUM' | 'HIGH'
export type AuthorizationStatus = 'ACTIVE' | 'EXPIRED' | 'REVOKED' | 'NOT_REQUIRED'
export type DataQualityStatus = 'VERIFIED' | 'REPORTED' | 'MISSING' | 'CONFLICT'
export type ReviewStatus = 'AUTO_APPLIED' | 'PENDING_REVIEW' | 'APPROVED' | 'REJECTED'
export type PostLoanSourceType =
  | 'BANK_INTERNAL_SIMULATED'
  | 'PLATFORM_AUTHORIZED_SIMULATED'
  | 'MERCHANT_SUBMITTED_SIMULATED'
  | 'MANUAL_VERIFIED_SIMULATED'

export interface PostLoanSourceStatus {
  source_id: string
  display_name: string
  source_type: PostLoanSourceType
  authorization_status: AuthorizationStatus
  scopes: string[]
  last_synced_at: string | null
  expires_at: string | null
  freshness_hours: number | null
  quality_status: DataQualityStatus
  verified: boolean
  record_count: number
}

export interface PostLoanReview {
  review_id: string
  review_month: string
  action: PostLoanAction
  current_limit: number
  candidate_limit: number
  proposed_limit: number
  outstanding_principal: number
  alert_level: PostLoanAlertLevel
  reason_codes: string[]
  reasons: string[]
  status: ReviewStatus
  next_review_date: string
  policy_version: string
  reviewer_note: string | null
}

export interface PostLoanSnapshot {
  month_index: number
  month: string
  observed_at: string
  received_at: string
  repayment: {
    due_date: string
    scheduled_amount: number
    paid_amount: number
    payment_date: string | null
    days_past_due: number
    on_time: boolean
  }
  operating: {
    receipts: number
    receipt_mom_growth: number | null
    orders: number
    refund_rate: number
    complaint_count: number
    cash_balance: number
    limit_utilization: number
    compliant_use_ratio: number
  }
  models: {
    operating_credit_score: number
    credit_grade: 'A' | 'B' | 'C' | 'D' | 'E'
    anomaly_score: number
    anomaly_risk: 'LOW' | 'MEDIUM' | 'HIGH'
    max_p90_funding_gap: number
    cash_gap_risk: 'LOW' | 'MEDIUM' | 'HIGH'
    confidence: Confidence
    score_model_version: string
    anomaly_model_version: string
    cash_gap_model_version: string
  }
  review: PostLoanReview
  source_ids: string[]
  data_quality_status: DataQualityStatus
}

export interface PostLoanAlert {
  alert_id: string
  merchant_id: string
  occurred_at: string
  level: PostLoanAlertLevel
  alert_type: string
  title: string
  description: string
  status: 'OPEN' | 'ACKNOWLEDGED' | 'CLOSED'
  evidence_refs: string[]
}

export interface MerchantSubmission {
  submission_id: string
  merchant_id: string
  category: 'OFF_BANK_STATEMENT' | 'CONTRACT' | 'PURPOSE_PROOF' | 'EXPLANATION'
  description: string
  file_name: string | null
  submitted_at: string
  source_type: 'MERCHANT_SUBMITTED_SIMULATED'
  verification_status: 'PENDING' | 'VERIFIED' | 'REJECTED'
}

export interface PostLoanTimeline {
  merchant_id: DemoMerchantId
  merchant_name: string
  scenario_name: string
  scenario_description: string
  simulated: true
  as_of_month: string
  current_month_index: number
  total_months: 12
  loan_account: {
    loan_id: string
    merchant_id: string
    initial_limit: number
    current_limit: number
    used_limit: number
    outstanding_principal: number
    available_limit: number
    disbursed_at: string
    status: 'ACTIVE' | 'FROZEN' | 'CLOSED'
  }
  source_statuses: PostLoanSourceStatus[]
  snapshots: PostLoanSnapshot[]
  alerts: PostLoanAlert[]
  submissions: MerchantSubmission[]
  current_review: PostLoanReview
  policy_notes: string[]
}
