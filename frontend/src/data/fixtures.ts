import normalRequestJson from '../../../docs/api_examples/full_analysis_normal_request.json'
import normalResponseJson from '../../../docs/api_examples/full_analysis_normal_response.json'
import type {
  ApplicationContext,
  ApplicationDraft,
  ConnectorId,
  DataGroupId,
  DemoCasePayload,
  FullAnalysisRequest,
  FullAnalysisResult,
  MaterialEvidence,
} from '../types'

const fallbackRequest = normalRequestJson as unknown as FullAnalysisRequest
const fallbackResponse = normalResponseJson as FullAnalysisResult

export const fallbackDemoCase: DemoCasePayload = {
  merchant_id: 'M001',
  case_label: '审批建议案例',
  case_description: '规则结果为审批建议，仍不代表真实银行承诺。',
  expected_risk: fallbackResponse.overall_risk,
  expected_decision: fallbackResponse.overall_decision,
  applicant: {
    merchant_name: '宜人美发生活馆',
    industry: '美容美发',
    social_credit_code: '91310000MA1DEMO001',
    province: '上海市',
    city: '上海市',
    address: '示范区惠民路 88 号',
    legal_name: '李女士',
    legal_phone: '13800000001',
    legal_id_number: '310101199001010011',
    contact_name: '李女士',
    contact_phone: '13800000001',
    contact_id_number: '310101199001010011',
    requested_amount: 500000,
  },
  merchant: fallbackRequest.merchant,
  anomaly: fallbackRequest.anomaly || {},
  cash_gap: fallbackRequest.cash_gap || {},
  materials: fallbackRequest.application.materials,
}

export function getDraftForCase(demoCase: DemoCasePayload): ApplicationDraft {
  const applicant = demoCase.applicant
  return {
    merchantName: applicant.merchant_name,
    industry: applicant.industry,
    socialCreditCode: applicant.social_credit_code,
    province: applicant.province,
    city: applicant.city,
    address: applicant.address,
    legalName: applicant.legal_name,
    legalPhone: applicant.legal_phone,
    legalIdNumber: applicant.legal_id_number,
    contactName: applicant.contact_name,
    contactPhone: applicant.contact_phone,
    contactIdNumber: applicant.contact_id_number,
    requestedAmount: applicant.requested_amount,
  }
}

export function getMerchantIdForCase(demoCase: DemoCasePayload): string {
  return demoCase.merchant_id
}

export function buildAnalysisRequest(
  demoCase: DemoCasePayload,
  draft: ApplicationDraft,
  identityVerified: boolean,
  uploadedDataGroups: DataGroupId[],
  authorizedSources: ConnectorId[],
  consentConfirmed: boolean,
  consentedAt: string | null,
  materials: MaterialEvidence[],
): FullAnalysisRequest {
  const merchant = structuredClone(demoCase.merchant) as {
    profile: string
    structural: {
      merchant_name: string
      industry: string
      requested_amount: number
      [key: string]: unknown
    }
    [key: string]: unknown
  }
  merchant.profile = 'v5_current'
  merchant.structural.merchant_name = draft.merchantName.trim()
  merchant.structural.industry = draft.industry
  merchant.structural.requested_amount = draft.requestedAmount

  const application: ApplicationContext = {
    social_credit_code: draft.socialCreditCode.trim().toUpperCase(),
    province: draft.province.trim(),
    city: draft.city.trim(),
    operating_address: `${draft.province.trim()}${draft.city.trim()}${draft.address.trim()}`,
    legal_name: draft.legalName.trim(),
    legal_phone: draft.legalPhone.trim(),
    legal_id_number: draft.legalIdNumber.trim().toUpperCase() || null,
    contact_name: draft.contactName.trim(),
    contact_phone: draft.contactPhone.trim(),
    contact_id_number: draft.contactIdNumber.trim().toUpperCase() || null,
    identity_verified: identityVerified,
    uploaded_data_groups: uploadedDataGroups,
    authorized_sources: authorizedSources,
    consent_confirmed: consentConfirmed,
    consented_at: consentedAt,
    materials,
  }

  return {
    application,
    merchant,
    anomaly: structuredClone(demoCase.anomaly),
    cash_gap: structuredClone(demoCase.cash_gap),
  }
}
