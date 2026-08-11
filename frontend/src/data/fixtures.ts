import normalRequestJson from '../../../docs/api_examples/full_analysis_normal_request.json'
import normalResponseJson from '../../../docs/api_examples/full_analysis_normal_response.json'
import reviewRequestJson from '../../../docs/api_examples/full_analysis_review_request.json'
import reviewResponseJson from '../../../docs/api_examples/full_analysis_review_response.json'
import type {
  ApplicationDraft,
  ApplicationContext,
  ConnectorId,
  DataGroupId,
  DemoCase,
  FullAnalysisRequest,
  FullAnalysisResult,
  MaterialEvidence,
} from '../types'

export const normalResponse = normalResponseJson as FullAnalysisResult
export const reviewResponse = reviewResponseJson as FullAnalysisResult

const drafts: Record<DemoCase, ApplicationDraft> = {
  normal: {
    merchantName: '宜人美发生活馆',
    industry: '美容美发',
    socialCreditCode: '91310000MA1DEMO001',
    address: '上海市示范区惠民路 88 号',
    legalName: '李女士',
    contactPhone: '13800000001',
    requestedAmount: 500000,
  },
  review: {
    merchantName: '欣悦美发工作室',
    industry: '美容美发',
    socialCreditCode: '91310000MA1DEMO005',
    address: '上海市示范区惠民路 188 号',
    legalName: '王女士',
    contactPhone: '13800000005',
    requestedAmount: 300000,
  },
}

export function getDraftForCase(demoCase: DemoCase): ApplicationDraft {
  return structuredClone(drafts[demoCase])
}

export function getMerchantIdForCase(demoCase: DemoCase): string {
  return demoCase === 'normal' ? 'M001' : 'M005'
}

export function buildAnalysisRequest(
  demoCase: DemoCase,
  draft: ApplicationDraft,
  identityVerified: boolean,
  uploadedDataGroups: DataGroupId[],
  authorizedSources: ConnectorId[],
  consentConfirmed: boolean,
  consentedAt: string | null,
  materials: MaterialEvidence[],
): FullAnalysisRequest {
  const source = demoCase === 'normal' ? normalRequestJson : reviewRequestJson
  const request = structuredClone(source) as {
    merchant: {
      merchant_id: string
      profile: string
      structural: {
        merchant_name: string
        requested_amount: number
        [key: string]: unknown
      }
      [key: string]: unknown
    }
    application: ApplicationContext
    anomaly?: Record<string, unknown> | null
    cash_gap?: Record<string, unknown> | null
    [key: string]: unknown
  }

  request.application = {
    social_credit_code: draft.socialCreditCode.trim().toUpperCase(),
    operating_address: draft.address.trim(),
    legal_name: draft.legalName.trim(),
    contact_phone: draft.contactPhone.trim(),
    identity_verified: identityVerified,
    uploaded_data_groups: uploadedDataGroups,
    authorized_sources: authorizedSources,
    consent_confirmed: consentConfirmed,
    consented_at: consentedAt,
    materials,
  }
  request.merchant.profile = 'v5_current'
  request.merchant.structural.merchant_name = draft.merchantName.trim()
  request.merchant.structural.industry = draft.industry
  request.merchant.structural.requested_amount = draft.requestedAmount
  return request
}

export function getMockResult(demoCase: DemoCase): FullAnalysisResult {
  return structuredClone(
    demoCase === 'normal' ? normalResponse : reviewResponse,
  )
}
