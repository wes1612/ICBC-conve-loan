import type { FullAnalysisResult } from './types'

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
  request: Record<string, unknown>,
): Promise<FullAnalysisResult> {
  const response = await fetch(`${API_BASE_URL}/api/v1/ml/full-analysis`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })

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
