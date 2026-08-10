import { useEffect, useState } from 'react'
import { checkHealth, runFullAnalysis } from './api'
import { buildAnalysisRequest, getMockResult } from './data/fixtures'
import type { ApplicationDraft, DataSource, DemoCase, FullAnalysisResult } from './types'
import { Icon } from './components/Icon'
import { HomePage } from './pages/HomePage'
import { IdentityPage } from './pages/IdentityPage'
import { VerifyPage } from './pages/VerifyPage'
import { DataPage } from './pages/DataPage'
import { AuthorizePage } from './pages/AuthorizePage'
import { ResultsPage } from './pages/ResultsPage'

const steps = [
  { key: 'home', label: '申请首页' },
  { key: 'identity', label: '主体资料' },
  { key: 'verify', label: '法人核验' },
  { key: 'data', label: '经营资料' },
  { key: 'authorize', label: '数据授权' },
  { key: 'results', label: '授信报告' },
] as const

type StepKey = (typeof steps)[number]['key']

const initialDraft: ApplicationDraft = {
  merchantName: '宜人美发生活馆',
  industry: '美容美发',
  socialCreditCode: '91310000MA1DEMO001',
  address: '上海市示范区惠民路 88 号',
  legalName: '李女士',
  contactPhone: '13800000001',
  requestedAmount: 500000,
}

function App() {
  const [step, setStep] = useState<StepKey>('home')
  const [furthest, setFurthest] = useState(0)
  const [demoCase, setDemoCase] = useState<DemoCase>('normal')
  const [draft, setDraft] = useState<ApplicationDraft>(initialDraft)
  const [apiOnline, setApiOnline] = useState<boolean | null>(null)
  const [analyzing, setAnalyzing] = useState(false)
  const [analysisError, setAnalysisError] = useState<string | null>(null)
  const [result, setResult] = useState<FullAnalysisResult | null>(null)
  const [source, setSource] = useState<DataSource>('mock')

  useEffect(() => {
    checkHealth().then(setApiOnline)
  }, [])

  const go = (next: StepKey) => {
    const index = steps.findIndex((item) => item.key === next)
    setFurthest((value) => Math.max(value, index))
    setStep(next)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const changeCase = (next: DemoCase) => {
    setDemoCase(next)
    setResult(null)
    setDraft((value) => ({
      ...value,
      merchantName: next === 'normal' ? '宜人美发生活馆' : '欣悦美发工作室',
      socialCreditCode: next === 'normal' ? '91310000MA1DEMO001' : '91310000MA1DEMO005',
      requestedAmount: next === 'normal' ? 500000 : 300000,
    }))
  }

  const analyze = async () => {
    setAnalyzing(true)
    setAnalysisError(null)
    const request = buildAnalysisRequest(demoCase, draft)
    const startedAt = Date.now()
    try {
      if (!apiOnline) throw new Error('offline')
      const response = await runFullAnalysis(request)
      setResult(response)
      setSource('api')
    } catch (error) {
      setResult(getMockResult(demoCase))
      setSource('mock')
      setAnalysisError(error instanceof Error && error.message !== 'offline' ? error.message : '本地后端当前未连接。')
    }
    const remaining = Math.max(0, 1250 - (Date.now() - startedAt))
    window.setTimeout(() => {
      setAnalyzing(false)
      go('results')
    }, remaining)
  }

  const activeIndex = steps.findIndex((item) => item.key === step)

  return (
    <div className="app-shell">
      <header className="site-header">
        <div className="page-shell site-header__inner">
          <button className="brand" onClick={() => go('home')} aria-label="返回申请首页">
            <span className="brand__mark">融</span>
            <span><strong>融策</strong><small>小微信用工作台</small></span>
          </button>
          <nav className="top-nav" aria-label="主要导航">
            <button className={step === 'home' ? 'is-active' : ''} onClick={() => go('home')}>申请测算</button>
            <button className={step === 'results' ? 'is-active' : ''} onClick={() => result && go('results')} disabled={!result}>分析报告</button>
          </nav>
          <div className="header-meta">
            <span className={`header-status ${apiOnline ? 'is-online' : ''}`}><i />{apiOnline === null ? '连接中' : apiOnline ? '服务在线' : '演示模式'}</span>
            <span className="competition-tag">工商银行杯 · MVP</span>
          </div>
        </div>
      </header>

      {step !== 'home' && (
        <div className="stepper-wrap">
          <ol className="stepper page-shell">
            {steps.slice(1).map((item, index) => {
              const realIndex = index + 1
              const done = realIndex < activeIndex
              const current = realIndex === activeIndex
              return (
                <li className={done ? 'is-done' : current ? 'is-current' : ''} key={item.key}>
                  <button onClick={() => realIndex <= furthest && go(item.key)} disabled={realIndex > furthest} aria-current={current ? 'step' : undefined}>
                    <span>{done ? <Icon name="check" size={14} /> : `0${realIndex}`}</span>
                    <strong>{item.label}</strong>
                  </button>
                </li>
              )
            })}
          </ol>
        </div>
      )}

      {step === 'home' && <HomePage demoCase={demoCase} onCaseChange={changeCase} onStart={() => go('identity')} />}
      {step === 'identity' && <IdentityPage value={draft} onChange={setDraft} onBack={() => go('home')} onNext={() => go('verify')} />}
      {step === 'verify' && <VerifyPage legalName={draft.legalName} onBack={() => go('identity')} onNext={() => go('data')} />}
      {step === 'data' && <DataPage onBack={() => go('verify')} onNext={() => go('authorize')} />}
      {step === 'authorize' && <AuthorizePage demoCase={demoCase} analyzing={analyzing} apiOnline={apiOnline} error={analysisError} onBack={() => go('data')} onAnalyze={analyze} />}
      {step === 'results' && result && <ResultsPage data={result} source={source} onRestart={() => go('home')} onBack={() => go('authorize')} />}

      <footer className="site-footer">
        <div className="page-shell"><span>融策 · 消费供给动态授信 MVP</span><span>可解释评分 · 异常证据 · 资金情景</span><span>仅供竞赛演示</span></div>
      </footer>
    </div>
  )
}

export default App
