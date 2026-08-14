import type {
  AiReportSummary,
  AssistantMessageRequest,
  AssistantReply,
  FullAnalysisRequest,
  FullAnalysisResult,
  MaterialEvidence,
  MaterialGroupId,
} from './types'

export const AI_UNAVAILABLE_MESSAGE = '智能解读暂不可用，原有五步流程和授信报告不受影响。'

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
).replace(/\/$/, '')

export interface ApiIssue {
  path: string
  message: string
}

export class ApiError extends Error {
  status: number
  issues: ApiIssue[]

  constructor(message: string, status: number, issues: ApiIssue[] = []) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.issues = issues
  }
}

function parseIssues(payload: unknown): ApiIssue[] {
  if (!payload || typeof payload !== 'object' || !('detail' in payload)) return []
  const detail = (payload as { detail?: unknown }).detail
  if (!Array.isArray(detail)) return []

  return detail.map((item) => {
    const issue = item as { loc?: Array<string | number>; msg?: string }
    return {
      path: (issue.loc || []).filter((part) => part !== 'body').join('.'),
      message: issue.msg || '字段校验失败',
    }
  })
}

export async function checkHealth(): Promise<boolean> {
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), 1800)
  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      signal: controller.signal,
    })
    return response.ok
  } catch {
    return false
  } finally {
    window.clearTimeout(timeout)
  }
}

export async function runFullAnalysis(
  request: FullAnalysisRequest,
): Promise<FullAnalysisResult> {
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), 15_000)
  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}/api/v1/ml/full-analysis`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
      signal: controller.signal,
    })
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError('分析请求超时，请检查后端服务后重试。', 0)
    }
    throw new ApiError('无法连接分析服务，请检查后端地址和网络。', 0)
  } finally {
    window.clearTimeout(timeout)
  }

  if (!response.ok) {
    const payload = await response.json().catch(() => null)
    const message =
      response.status === 422
        ? '部分资料未通过校验，请检查对应字段。'
        : '分析服务暂时不可用，请稍后重试。'
    throw new ApiError(message, response.status, parseIssues(payload))
  }

  return (await response.json()) as FullAnalysisResult
}

function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer)
  const chunkSize = 0x8000
  let binary = ''
  for (let offset = 0; offset < bytes.length; offset += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(offset, offset + chunkSize))
  }
  return window.btoa(binary)
}

async function materialError(response: Response): Promise<ApiError> {
  const payload = await response.json().catch(() => null) as { detail?: unknown } | null
  const detail = typeof payload?.detail === 'string' ? payload.detail : null
  return new ApiError(detail || '材料解析失败，请检查文件后重试。', response.status)
}

export async function parseMaterial(
  merchantId: string,
  group: MaterialGroupId,
  file: File,
): Promise<MaterialEvidence> {
  if (file.size > 5 * 1024 * 1024) {
    throw new ApiError('单个材料不能超过 5 MB。', 0)
  }
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), 20_000)
  try {
    const content = arrayBufferToBase64(await file.arrayBuffer())
    const response = await fetch(`${API_BASE_URL}/api/v1/materials/parse`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        merchant_id: merchantId,
        group,
        file_name: file.name,
        media_type: file.type || 'application/octet-stream',
        size_bytes: file.size,
        content_base64: content,
      }),
      signal: controller.signal,
    })
    if (!response.ok) throw await materialError(response)
    return (await response.json()) as MaterialEvidence
  } catch (error) {
    if (error instanceof ApiError) throw error
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError('材料解析超时，请检查后端服务后重试。', 0)
    }
    throw new ApiError('无法连接材料解析服务，请确认后端已经启动。', 0)
  } finally {
    window.clearTimeout(timeout)
  }
}

export async function downloadDemoMaterial(
  merchantId: string,
  group: MaterialGroupId,
  fileName: string,
): Promise<File> {
  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}/api/v1/materials/demo/${merchantId}/${group}`)
  } catch {
    throw new ApiError('无法下载演示材料，请确认后端已经启动。', 0)
  }
  if (!response.ok) throw await materialError(response)
  const blob = await response.blob()
  return new File([blob], `${merchantId}_${fileName}`, { type: blob.type })
}

async function aiError(response: Response): Promise<ApiError> {
  const payload = await response.json().catch(() => null) as { detail?: unknown } | null
  const detail = typeof payload?.detail === 'string' ? payload.detail : null
  return new ApiError(detail || AI_UNAVAILABLE_MESSAGE, response.status)
}

async function postAi<T>(path: string, body: unknown, timeoutMs: number): Promise<T> {
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs)
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: controller.signal,
    })
    if (!response.ok) throw await aiError(response)
    return (await response.json()) as T
  } catch (error) {
    if (error instanceof ApiError) throw error
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError(AI_UNAVAILABLE_MESSAGE, 0)
    }
    throw new ApiError(AI_UNAVAILABLE_MESSAGE, 0)
  } finally {
    window.clearTimeout(timeout)
  }
}

export function requestAssistantMessage(
  request: AssistantMessageRequest,
): Promise<AssistantReply> {
  return postAi<AssistantReply>('/api/v1/assistant/messages', request, 30_000)
}

export function requestAiReportSummary(
  analysis: FullAnalysisResult,
): Promise<AiReportSummary> {
  return postAi<AiReportSummary>('/api/v1/ai/report-summary', { analysis }, 40_000)
}

export function describeApiError(error: unknown): string {
  if (!(error instanceof ApiError)) return '分析失败，请稍后重试。'
  if (!error.issues.length) return error.message
  const details = error.issues
    .slice(0, 4)
    .map((issue) => `${issue.path || '请求'}：${issue.message}`)
    .join('；')
  return `${error.message} ${details}`
}
