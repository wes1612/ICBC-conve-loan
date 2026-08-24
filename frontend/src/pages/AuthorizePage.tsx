import { useState } from 'react'
import type { AnalysisMode, ConnectorId } from '../types'
import { Icon } from '../components/Icon'
import { Button, Eyebrow, InfoNote } from '../components/Ui'

interface AuthorizePageProps {
  analysisMode: AnalysisMode
  analyzing: boolean
  apiOnline: boolean | null
  error: string | null
  contactPhone: string
  enabled: ConnectorId[]
  consentConfirmed: boolean
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
  icon: string
}> = [
  { id: 'bank', name: '银行经营流水', type: '评分、异常与现金流', available: true, required: true, icon: '/connector-icons/icbc.webp' },
  { id: 'meituan', name: '美团订单与评价', type: '订单与口碑交叉验证', available: true, required: true, icon: '/connector-icons/meituan.jpg' },
  { id: 'enterprise', name: '公开工商信息', type: '主体身份核验', available: true, required: true, icon: '/connector-icons/national-emblem.webp' },
  { id: 'unionpay', name: '银联收单', type: '后续真实接口', available: false, required: false, icon: '/connector-icons/union-pay.png' },
  { id: 'alipay', name: '支付宝经营数据', type: '后续真实接口', available: false, required: false, icon: '/connector-icons/alipay.png' },
  { id: 'wechat', name: '微信经营数据', type: '后续真实接口', available: false, required: false, icon: '/connector-icons/wechat.jpg' },
  { id: 'douyin', name: '抖音团购与抖音账户', type: '后续真实接口', available: false, required: false, icon: '/connector-icons/tiktok.jpg' },
  { id: 'xiaohongshu', name: '小红书账号数据', type: '后续真实接口', available: false, required: false, icon: '/connector-icons/rednote.jpg' },
]

const requiredSourceIds = connectors.filter((item) => item.required).map((item) => item.id)
const availableCount = connectors.filter((item) => item.available).length

function maskedPhone(phone: string) {
  const digits = phone.replace(/\D/g, '')
  if (digits.length < 7) return phone || '132****1919'
  return `${digits.slice(0, 3)}****${digits.slice(-4)}`
}

export function AuthorizePage({
  analysisMode,
  analyzing,
  apiOnline,
  error,
  contactPhone,
  enabled,
  consentConfirmed,
  prerequisitesReady,
  onEnabledChange,
  onConsentChange,
  onBack,
  onAnalyze,
}: AuthorizePageProps) {
  const [verificationCode, setVerificationCode] = useState('')
  const [codeSent, setCodeSent] = useState(false)
  const requiredReady = requiredSourceIds.every((id) => enabled.includes(id))
  const ready = prerequisitesReady && requiredReady && consentConfirmed

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
      <div className="workflow__intro workflow__intro--authorize">
        <div>
          <Eyebrow>04 · 数据授权与分析</Eyebrow>
          <p>工商银行可通过授权获取企业在相关平台的信息，综合评价企业经营状况。授权数据的来源和数量可能影响最终评判结果。请合理选择。</p>
        </div>
        <div className={`backend-state ${analysisMode === 'mock' || apiOnline ? 'is-online' : 'is-offline'}`}><i /><span>{serviceLabel}</span></div>
      </div>

      <div className="authorize-layout">
        <section className="connector-panel">
          <div className="panel-heading"><div><h2>数据来源</h2><p>8 个接口可供授权，当前开放 {availableCount} 项 · 已授权 {enabled.length} 项</p></div><Icon name="lock" /></div>
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
                  <span className={`connector-logo connector-logo--${item.id}`} aria-hidden="true"><img src={item.icon} alt="" /></span>
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
          <div className="phone-verification" aria-label="手机号验证">
            <span>手机号：<strong>{maskedPhone(contactPhone)}</strong></span>
            <button type="button" onClick={() => setCodeSent(true)} disabled={analyzing}>{codeSent ? '重新发送' : '发送验证码'}</button>
            <input
              value={verificationCode}
              onChange={(event) => setVerificationCode(event.target.value.replace(/\D/g, '').slice(0, 6))}
              inputMode="numeric"
              placeholder={codeSent ? '输入验证码' : ''}
              aria-label="短信验证码"
              disabled={analyzing}
            />
          </div>
        </section>

        <section className="analysis-panel">
          <div className="analysis-core">
            <div className="analysis-core__mark"><Icon name="spark" size={34} /></div>
            <h2>{ready ? '资料与授权已准备完成' : '等待完成授权'}</h2>
            <p>接口失败会保留在本页并显示原因，不会自动生成授信结果。</p>
          </div>
          {error && <InfoNote tone="warning">{error} 当前没有生成任何授信结论，请修正后重试。</InfoNote>}
          <Button icon="arrow" onClick={onAnalyze} disabled={analyzing || !ready}>{analyzing ? '分析进行中…' : '运行综合分析'}</Button>
        </section>
      </div>

      <div className="workflow__actions">
        <Button variant="ghost" onClick={onBack} disabled={analyzing}>返回</Button>
      </div>
    </main>
  )
}
