import { useEffect, useState } from 'react'
import { checkHealth, describeApiError, runFullAnalysis } from './api'
import {
  buildAnalysisRequest,
  getDraftForCase,
  getMerchantIdForCase,
  getMockResult,
} from './data/fixtures'
import type {
  AnalysisMode,
  ApplicationDraft,
  ConnectorId,
  DataGroupId,
  DataSource,
  DemoCase,
  FullAnalysisResult,
  MaterialEvidence,
  PortalMode,
} from './types'
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

const urlParameters = new URLSearchParams(window.location.search)
const portal: PortalMode = urlParameters.get('portal') === 'reviewer' ? 'reviewer' : 'merchant'
const demoControlsEnabled = portal === 'reviewer' || urlParameters.get('demo') === '1'

function App() {
  const [step, setStep] = useState<StepKey>('home')
  const [furthest, setFurthest] = useState(0)
  const [demoCase, setDemoCase] = useState<DemoCase>('normal')
  const [analysisMode, setAnalysisMode] = useState<AnalysisMode>('api')
  const [draft, setDraft] = useState<ApplicationDraft>(() => getDraftForCase('normal'))
  const [identityVerified, setIdentityVerified] = useState(false)
  const [materials, setMaterials] = useState<MaterialEvidence[]>([])
  const [authorizedSources, setAuthorizedSources] = useState<ConnectorId[]>([])
  const [consentConfirmed, setConsentConfirmed] = useState(false)
  const [consentedAt, setConsentedAt] = useState<string | null>(null)
  const [apiOnline, setApiOnline] = useState<boolean | null>(null)
  const [analyzing, setAnalyzing] = useState(false)
  const [analysisError, setAnalysisError] = useState<string | null>(null)
  const [result, setResult] = useState<FullAnalysisResult | null>(null)
  const [source, setSource] = useState<DataSource>('api')
  const uploadedGroups = materials
    .map((material) => material.group)
    .filter((group): group is DataGroupId => ['cashflow', 'statement', 'tax', 'plan'].includes(group))
  const dataReady = (['cashflow', 'statement', 'tax', 'plan'] as DataGroupId[])
    .every((group) => uploadedGroups.includes(group))

  useEffect(() => {
    checkHealth().then(setApiOnline)
  }, [])

  const go = (next: StepKey) => {
    const index = steps.findIndex((item) => item.key === next)
    setFurthest((value) => Math.max(value, index))
    setStep(next)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const resetWorkflow = (nextCase: DemoCase) => {
    setDraft(getDraftForCase(nextCase))
    setIdentityVerified(false)
    setMaterials([])
    setAuthorizedSources([])
    setConsentConfirmed(false)
    setConsentedAt(null)
    setAnalysisError(null)
    setResult(null)
    setFurthest(0)
  }

  const changeCase = (next: DemoCase) => {
    setDemoCase(next)
    resetWorkflow(next)
  }

  const changeDraft = (next: ApplicationDraft) => {
    if (
      next.legalName !== draft.legalName
      || next.socialCreditCode !== draft.socialCreditCode
    ) {
      setIdentityVerified(false)
      setMaterials([])
    }
    setDraft(next)
    setResult(null)
  }

  const changeConsent = (confirmed: boolean) => {
    setConsentConfirmed(confirmed)
    setConsentedAt(confirmed ? new Date().toISOString() : null)
  }

  const changeAnalysisMode = (next: AnalysisMode) => {
    setAnalysisMode(next)
    setAnalysisError(null)
    setResult(null)
  }

  const analyze = async () => {
    setAnalyzing(true)
    setAnalysisError(null)
    setResult(null)
    const request = buildAnalysisRequest(
      demoCase,
      draft,
      identityVerified,
      uploadedGroups,
      authorizedSources,
      consentConfirmed,
      consentedAt,
      materials,
    )
    const startedAt = Date.now()

    try {
      if (analysisMode === 'mock') {
        setResult(getMockResult(demoCase))
        setSource('mock')
      } else {
        const online = await checkHealth()
        setApiOnline(online)
        if (!online) throw new Error('分析服务当前离线，请启动后端后重试。')
        const response = await runFullAnalysis(request)
        setResult(response)
        setSource('api')
      }

      const remaining = Math.max(0, 900 - (Date.now() - startedAt))
      if (remaining) await new Promise((resolve) => window.setTimeout(resolve, remaining))
      setAnalyzing(false)
      go('results')
    } catch (error) {
      setAnalyzing(false)
      setResult(null)
      setAnalysisError(
        error instanceof Error && error.message.startsWith('分析服务当前离线')
          ? error.message
          : describeApiError(error),
      )
    }
  }

  const restart = () => {
    resetWorkflow(demoCase)
    setStep('home')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const activeIndex = steps.findIndex((item) => item.key === step)

  return (
    <div className="app-shell">
      <header className="site-header">
        <div className="page-shell site-header__inner">
          <button className="brand" onClick={() => go('home')} aria-label="返回申请首页">
            <span className="brand__mark">融</span>
            <span><strong>融策</strong><small>{portal === 'merchant' ? '小微信用工作台' : '银行风险审核台'}</small></span>
          </button>
          <nav className="top-nav" aria-label="主要导航">
            <button className={step === 'home' ? 'is-active' : ''} onClick={() => go('home')}>{portal === 'merchant' ? '申请测算' : '审核案例'}</button>
            <button className={step === 'results' ? 'is-active' : ''} onClick={() => result && go('results')} disabled={!result}>{portal === 'merchant' ? '分析报告' : '风险审核'}</button>
          </nav>
          <div className="header-meta">
            <span className={`header-status ${apiOnline ? 'is-online' : ''}`}><i />{apiOnline === null ? '连接中' : apiOnline ? '服务在线' : '服务离线'}</span>
            <span className="competition-tag">{portal === 'merchant' ? '商户端' : '银行端'} · MVP</span>
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

      {step === 'home' && (
        <HomePage
          portal={portal}
          demoCase={demoCase}
          analysisMode={analysisMode}
          showDemoControls={demoControlsEnabled}
          onCaseChange={changeCase}
          onModeChange={changeAnalysisMode}
          onStart={() => go('identity')}
        />
      )}
      {step === 'identity' && <IdentityPage value={draft} onChange={changeDraft} onBack={() => go('home')} onNext={() => go('verify')} />}
      {step === 'verify' && <VerifyPage legalName={draft.legalName} verified={identityVerified} onVerifiedChange={setIdentityVerified} onBack={() => go('identity')} onNext={() => go('data')} />}
      {step === 'data' && (
        <DataPage
          merchantId={getMerchantIdForCase(demoCase)}
          demoCase={demoCase}
          analysisMode={analysisMode}
          materials={materials}
          onChange={setMaterials}
          onBack={() => go('verify')}
          onNext={() => go('authorize')}
        />
      )}
      {step === 'authorize' && (
        <AuthorizePage
          demoCase={demoCase}
          analysisMode={analysisMode}
          analyzing={analyzing}
          apiOnline={apiOnline}
          error={analysisError}
          enabled={authorizedSources}
          consentConfirmed={consentConfirmed}
          prerequisitesReady={identityVerified && dataReady}
          onEnabledChange={setAuthorizedSources}
          onConsentChange={changeConsent}
          onBack={() => go('data')}
          onAnalyze={analyze}
        />
      )}
      {step === 'results' && result && <ResultsPage data={result} source={source} portal={portal} onRestart={restart} onBack={() => go('authorize')} />}

      <footer className="site-footer">
        <div className="page-shell"><span>融策 · 消费供给动态授信 MVP</span><span>{portal === 'merchant' ? '商户申请与经营建议' : '风险证据与审核处置'}</span><span>仅供竞赛演示</span></div>
      </footer>
    </div>
  )
}

export default App
