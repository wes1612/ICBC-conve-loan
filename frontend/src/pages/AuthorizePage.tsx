import { useEffect, useState } from 'react'
import type { AnalysisMode, ConnectorId, DemoCase } from '../types'
import { Icon } from '../components/Icon'
import { Button, Eyebrow, InfoNote } from '../components/Ui'

interface AuthorizePageProps {
  demoCase: DemoCase
  analysisMode: AnalysisMode
  analyzing: boolean
  apiOnline: boolean | null
  error: string | null
  enabled: ConnectorId[]
  consentConfirmed: boolean
  consentedAt: string | null
  prerequisitesReady: boolean
  onEnabledChange: (enabled: ConnectorId[]) => void
  onConsentChange: (confirmed: boolean) => void
  onBack: () => void
  onAnalyze: () => void
}

const connectors: Array<{
  id: ConnectorId
  name: string
  type: string
  available: boolean
  required: boolean
}> = [
  { id: 'bank', name: '银行经营流水', type: '评分、异常与现金流', available: true, required: true },
  { id: 'meituan', name: '美团订单与评价', type: '订单与口碑交叉验证', available: true, required: true },
  { id: 'enterprise', name: '公开工商信息', type: '主体身份核验', available: true, required: true },
  { id: 'unionpay', name: '银联收单', type: '后续真实接口', available: false, required: false },
  { id: 'alipay', name: '支付宝经营数据', type: '后续真实接口', available: false, required: false },
  { id: 'wechat', name: '微信经营数据', type: '后续真实接口', available: false, required: false },
  { id: 'douyin', name: '抖音团购与社媒', type: '后续真实接口', available: false, required: false },
  { id: 'xiaohongshu', name: '小红书口碑', type: '后续真实接口', available: false, required: false },
]

const requiredSourceIds = connectors.filter((item) => item.required).map((item) => item.id)
const availableCount = connectors.filter((item) => item.available).length

export function AuthorizePage({
  demoCase,
  analysisMode,
  analyzing,
  apiOnline,
  error,
  enabled,
  consentConfirmed,
  consentedAt,
  prerequisitesReady,
  onEnabledChange,
  onConsentChange,
  onBack,
  onAnalyze,
}: AuthorizePageProps) {
  const [progress, setProgress] = useState(0)
  const requiredReady = requiredSourceIds.every((id) => enabled.includes(id))
  const ready = prerequisitesReady && requiredReady && consentConfirmed

  useEffect(() => {
    if (!analyzing) {
      setProgress(0)
      return
    }
    const timer = window.setInterval(() => setProgress((value) => Math.min(92, value + 8)), 140)
    return () => window.clearInterval(timer)
  }, [analyzing])

  const toggle = (id: ConnectorId, available: boolean) => {
    if (!available) return
    onEnabledChange(enabled.includes(id) ? enabled.filter((item) => item !== id) : [...enabled, id])
  }

  const serviceLabel = analysisMode === 'mock'
    ? '固定样例模式 · 不请求后端'
    : apiOnline === null
      ? '检查分析服务…'
      : apiOnline
        ? '后端服务在线'
        : '后端离线 · 提交时将重新检查'

  return (
    <main className="workflow page-shell">
      <div className="workflow__intro">
        <div>
          <Eyebrow>步骤 04 · 数据授权与分析</Eyebrow>
          <h1>授权边界，由企业决定。</h1>
          <p>每项授权均由申请人主动选择并记录确认时间；未授权的数据不能随分析请求发送。</p>
        </div>
        <div className={`backend-state ${analysisMode === 'mock' || apiOnline ? 'is-online' : 'is-offline'}`}><i /><span>{serviceLabel}</span></div>
      </div>

      <div className="authorize-layout">
        <section className="connector-panel">
          <div className="panel-heading"><div><h2>数据来源</h2><p>已授权 {enabled.length} / {availableCount} 项可用来源</p></div><Icon name="lock" /></div>
          <div className="connector-list">
            {connectors.map((item) => {
              const active = enabled.includes(item.id)
              return (
                <button
                  key={item.id}
                  type="button"
                  className={`${active ? 'is-active' : ''} ${!item.available ? 'is-unavailable' : ''}`}
                  onClick={() => toggle(item.id, item.available)}
                  disabled={!item.available || analyzing}
                  aria-pressed={active}
                >
                  <span className="connector-logo">{item.name.slice(0, 1)}</span>
                  <span><strong>{item.name}{item.required ? ' *' : ''}</strong><small>{item.type} · {item.available ? '需主动授权' : '尚未接入'}</small></span>
                  <i className="toggle"><b /></i>
                </button>
              )
            })}
          </div>
          <label className="consent-check">
            <input type="checkbox" checked={consentConfirmed} onChange={(event) => onConsentChange(event.target.checked)} disabled={analyzing} />
            <span><strong>我已阅读并同意本次数据使用授权</strong><small>仅用于本次授信分析；取消授权后不能提交。</small></span>
          </label>
          <div className="consent-meta">
            <span>授权版本：consent_v1_2026_08</span>
            <span>{consentedAt ? '授权时间：' + new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(consentedAt)) : '授权时间：待确认'}</span>
            <span>用途范围：授信测算、异常核查、现金流预测与审计留痕</span>
          </div>
          {!ready && <InfoNote tone="warning">{!prerequisitesReady ? '主体核验或五份必交材料已发生变更，请返回补齐。' : '请授权三项带 * 的当前可用来源，并主动勾选数据使用授权。'}</InfoNote>}
        </section>

        <section className="analysis-panel">
          <div className="analysis-panel__case"><span>当前测试数据</span><strong>{demoCase === 'normal' ? 'M001 · 正常案例' : 'M005 · 人工复核案例'}</strong><small>{analysisMode === 'api' ? '真实请求 FastAPI · profile: v5_current' : '显式固定样例 · 不代表接口成功'}</small></div>
          <div className={`analysis-core ${analyzing ? 'is-running' : ''}`}>
            <div className="analysis-core__mark"><Icon name={analyzing ? 'refresh' : 'spark'} size={34} /></div>
            <h2>{analyzing ? '正在汇总三类分析…' : ready ? '资料与授权已准备完成' : '等待完成授权'}</h2>
            <p>{analyzing ? '经营评分、异常识别与资金缺口预测将由统一接口一次返回。' : '接口失败会保留在本页并显示原因，不会自动生成授信结果。'}</p>
            {analyzing && <div className="progress-track"><span style={{ width: `${progress}%` }} /></div>}
            {analyzing && <small>{progress < 34 ? '正在计算经营特征' : progress < 68 ? '正在核查交易异常' : '正在生成现金情景'}</small>}
          </div>
          {error && <InfoNote tone="warning">{error} 当前没有生成任何授信结论，请修正后重试。</InfoNote>}
          <Button icon="arrow" onClick={onAnalyze} disabled={analyzing || !ready}>{analyzing ? '分析进行中…' : '运行综合分析'}</Button>
          <div className="analysis-contract"><Icon name="shield" /><span><strong>接口契约 v0.4.0</strong>POST /api/v1/ml/full-analysis</span></div>
        </section>
      </div>

      <div className="workflow__actions">
        <Button variant="ghost" onClick={onBack} disabled={analyzing}>返回</Button>
      </div>
    </main>
  )
}
