import { useState } from 'react'
import { AI_UNAVAILABLE_MESSAGE, requestAiReportSummary } from '../api'
import type { AiReportSummary, FullAnalysisResult } from '../types'
import { Icon } from './Icon'

export function AiSummaryCard({ data }: { data: FullAnalysisResult }) {
  const [summary, setSummary] = useState<AiReportSummary | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const generate = async () => {
    setLoading(true)
    setError(null)
    try {
      setSummary(await requestAiReportSummary(data))
    } catch {
      setSummary(null)
      setError(AI_UNAVAILABLE_MESSAGE)
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="ai-summary-card report-card report-card--full">
      <div className="ai-summary-card__header">
        <div className="ai-summary-card__title">
          <span><Icon name="spark" size={22} /></span>
          <div><small>独立解释模块</small><h2>AI 智能解读</h2></div>
        </div>
        <button type="button" onClick={() => void generate()} disabled={loading}>
          {loading ? '正在解读…' : summary ? '重新生成' : '生成智能解读'}
        </button>
      </div>

      {!summary && !loading && !error && (
        <div className="ai-summary-card__empty">
          <p>基于现有结构化分析结果生成解释，不读取原始文件，也不修改评分、额度和审核结论。</p>
        </div>
      )}
      {loading && <div className="ai-summary-card__loading"><i /><span>正在核对结构化结果和证据编号</span></div>}
      {error && <div className="ai-summary-card__error"><Icon name="warning" size={18} /><div><strong>智能解读暂不可用</strong><p>原有评分、授信报告和五步流程仍然完整可用。</p></div></div>}

      {summary && (
        <div className="ai-summary-card__body">
          <p className="ai-summary-card__overview">{summary.overall_summary}</p>
          <div className="ai-summary-card__columns">
            <div><h3><Icon name="check" size={17} />有利因素</h3><ul>{summary.positive_factors.map((item) => <li key={item}>{item}</li>)}</ul></div>
            <div><h3><Icon name="warning" size={17} />风险因素</h3><ul>{summary.risk_factors.map((item) => <li key={item}>{item}</li>)}</ul></div>
          </div>
          <div className="ai-summary-card__detail"><h3>资金缺口解释</h3><p>{summary.cash_gap_interpretation}</p></div>
          <div className="ai-summary-card__detail"><h3>建议动作</h3><ol>{summary.recommended_actions.map((item) => <li key={item}>{item}</li>)}</ol></div>
          <div className="ai-summary-card__refs"><span>证据编号</span>{summary.evidence_refs.map((ref) => <code key={ref}>{ref}</code>)}</div>
          <p className="ai-summary-card__disclaimer"><Icon name="shield" size={16} />{summary.disclaimer}</p>
        </div>
      )}
    </section>
  )
}
