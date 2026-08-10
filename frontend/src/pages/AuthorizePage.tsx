import { useEffect, useState } from 'react'
import type { DemoCase } from '../types'
import { Icon } from '../components/Icon'
import { Button, Eyebrow, InfoNote } from '../components/Ui'

interface AuthorizePageProps {
  demoCase: DemoCase
  analyzing: boolean
  apiOnline: boolean | null
  error: string | null
  onBack: () => void
  onAnalyze: () => void
}

const connectors = [
  { id: 'bank', name: '银行经营流水', type: '核心', initial: true },
  { id: 'unionpay', name: '银联收单', type: '核心', initial: true },
  { id: 'alipay', name: '支付宝经营数据', type: '补充', initial: true },
  { id: 'wechat', name: '微信经营数据', type: '补充', initial: true },
  { id: 'meituan', name: '美团订单与评价', type: '补充', initial: true },
  { id: 'douyin', name: '抖音团购与社媒', type: '补充', initial: false },
  { id: 'xiaohongshu', name: '小红书口碑', type: '补充', initial: false },
  { id: 'enterprise', name: '公开工商信息', type: '核验', initial: true },
]

export function AuthorizePage({ demoCase, analyzing, apiOnline, error, onBack, onAnalyze }: AuthorizePageProps) {
  const [enabled, setEnabled] = useState(() => connectors.filter((item) => item.initial).map((item) => item.id))
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    if (!analyzing) {
      setProgress(0)
      return
    }
    const timer = window.setInterval(() => setProgress((value) => Math.min(92, value + 8)), 140)
    return () => window.clearInterval(timer)
  }, [analyzing])

  return (
    <main className="workflow page-shell">
      <div className="workflow__intro">
        <div>
          <Eyebrow>步骤 04 · 数据授权与分析</Eyebrow>
          <h1>授权边界，由企业决定。</h1>
          <p>生产环境应逐项取得授权并记录用途。当前按钮仅切换界面状态，不连接第三方账户。</p>
        </div>
        <div className={`backend-state ${apiOnline ? 'is-online' : 'is-offline'}`}><i /><span>{apiOnline === null ? '检查分析服务…' : apiOnline ? '后端服务在线' : '后端离线 · 将使用固定样例'}</span></div>
      </div>

      <div className="authorize-layout">
        <section className="connector-panel">
          <div className="panel-heading"><div><h2>数据来源</h2><p>已选择 {enabled.length} / {connectors.length} 项</p></div><Icon name="lock" /></div>
          <div className="connector-list">
            {connectors.map((item) => {
              const active = enabled.includes(item.id)
              return (
                <button key={item.id} className={active ? 'is-active' : ''} onClick={() => setEnabled((items) => active ? items.filter((id) => id !== item.id) : [...items, item.id])}>
                  <span className="connector-logo">{item.name.slice(0, 1)}</span>
                  <span><strong>{item.name}</strong><small>{item.type}数据 · 演示授权</small></span>
                  <i className="toggle"><b /></i>
                </button>
              )
            })}
          </div>
        </section>

        <section className="analysis-panel">
          <div className="analysis-panel__case"><span>当前联调样例</span><strong>{demoCase === 'normal' ? 'M001 · 正常授信' : 'M005 · 人工复核'}</strong><small>请求始终使用 profile: v5_current</small></div>
          <div className={`analysis-core ${analyzing ? 'is-running' : ''}`}>
            <div className="analysis-core__mark"><Icon name={analyzing ? 'refresh' : 'spark'} size={34} /></div>
            <h2>{analyzing ? '正在汇总三类分析…' : '资料已准备完成'}</h2>
            <p>{analyzing ? '经营评分、异常识别与资金缺口预测将由统一接口一次返回。' : '点击后优先调用真实后端；不可用时自动回退到仓库固定样例。'}</p>
            {analyzing && <div className="progress-track"><span style={{ width: `${progress}%` }} /></div>}
            {analyzing && <small>{progress < 34 ? '正在计算经营特征' : progress < 68 ? '正在核查交易异常' : '正在生成现金情景'}</small>}
          </div>
          {error && <InfoNote tone="warning">{error} 已保留页面资料并切换到固定联调响应。</InfoNote>}
          <Button icon="arrow" onClick={onAnalyze} disabled={analyzing}>{analyzing ? '分析进行中…' : '运行综合分析'}</Button>
          <div className="analysis-contract"><Icon name="shield" /><span><strong>接口契约 v0.2.0</strong>POST /api/v1/ml/full-analysis</span></div>
        </section>
      </div>

      <div className="workflow__actions">
        <Button variant="ghost" onClick={onBack} disabled={analyzing}>返回</Button>
      </div>
    </main>
  )
}
