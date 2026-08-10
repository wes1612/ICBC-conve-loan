import normalRequestJson from '../../../docs/api_examples/full_analysis_normal_request.json'
import normalResponseJson from '../../../docs/api_examples/full_analysis_normal_response.json'
import reviewRequestJson from '../../../docs/api_examples/full_analysis_review_request.json'
import reviewResponseJson from '../../../docs/api_examples/full_analysis_review_response.json'
import type {
  ApplicationDraft,
  DemoCase,
  FullAnalysisResult,
} from '../types'

export const normalResponse = normalResponseJson as FullAnalysisResult
export const reviewResponse = reviewResponseJson as FullAnalysisResult

export function buildAnalysisRequest(
  demoCase: DemoCase,
  draft: ApplicationDraft,
): Record<string, unknown> {
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
    [key: string]: unknown
  }

  request.merchant.profile = 'v5_current'
  request.merchant.structural.merchant_name = draft.merchantName
  request.merchant.structural.requested_amount = draft.requestedAmount
  return request
}

export function getMockResult(demoCase: DemoCase): FullAnalysisResult {
  return structuredClone(
    demoCase === 'normal' ? normalResponse : reviewResponse,
  )
}
