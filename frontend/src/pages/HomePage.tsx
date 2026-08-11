import type { AnalysisMode, DemoCase, PortalMode } from '../types'
import { Icon } from '../components/Icon'
import { Button, Eyebrow, InfoNote } from '../components/Ui'

interface HomePageProps {
  portal: PortalMode
  demoCase: DemoCase
  analysisMode: AnalysisMode
  showDemoControls: boolean
  onCaseChange: (value: DemoCase) => void
  onModeChange: (value: AnalysisMode) => void
  onStart: () => void
}

const capabilities = [
  { number: '01', title: '经营信用', text: '从稳定性、真实性、成长性与消费承接能力等维度形成可解释评分。' },
  { number: '02', title: '异常核查', text: '识别交易异常模式，输出原因码与可追溯证据，仅用于预警和人工复核。' },
  { number: '03', title: '缺口预测', text: '对未来三个月进行 P50 / P90 现金情景测算，识别流动性压力。' },
]

export function HomePage({ portal, demoCase, analysisMode, showDemoControls, onCaseChange, onModeChange, onStart }: HomePageProps) {
  const reviewer = portal === 'reviewer'
  return (
    <main>
      <section className="hero page-shell">
        <div className="hero__copy">
          <Eyebrow>{reviewer ? '银行风险审核 · 独立演示入口' : '小微经营 · 动态授信 MVP'}</Eyebrow>
          <h1>{reviewer ? <>让风险证据，成为<br /><em>可追溯的判断。</em></> : <>让经营数据，成为<br /><em>被看见的信用。</em></>}</h1>
          <p className="hero__lead">
            {reviewer
              ? '这是与商户端分离的银行审核演示入口。先生成一份测试申请，再查看评分门控、异常证据与流动性压力。'
              : '面向小微经营者的可解释授信工作台。一次提交资料，完成经营评分、异常识别与资金缺口测算。'}
          </p>
          <div className="hero__actions">
            <Button icon="arrow" onClick={onStart}>{reviewer ? '准备审核案例' : '开始授信测算'}</Button>
            <span className="hero__time"><i /> 演示流程约 3 分钟</span>
          </div>
          <InfoNote>
            页面展示为竞赛 MVP，不构成正式授信承诺。额度、利率与审批结果以银行最终审核为准。
          </InfoNote>
        </div>

        <div className="hero__visual" aria-label="授信能力概览">
          <div className="hero-orbit hero-orbit--one" />
          <div className="hero-orbit hero-orbit--two" />
          <div className="hero-score">
            <span>经营信用</span>
            <strong>{demoCase === 'normal' ? '90.7' : '61.1'}</strong>
            <small>示例评分 / 100</small>
          </div>
          <div className="floating-card floating-card--limit">
            <Icon name="bank" />
            <div><span>建议额度示例</span><strong>{demoCase === 'normal' ? '¥438,042' : '¥131,419'}</strong></div>
          </div>
          <div className="floating-card floating-card--risk">
            <span className={`status-dot status-dot--${demoCase}`} />
            <div><span>总体风险</span><strong>{demoCase === 'normal' ? '当前未发现显著风险' : '进入人工复核'}</strong></div>
          </div>
          <div className="hero-stamp"><Icon name="shield" size={34} /><span>结论可追溯</span></div>
        </div>
      </section>

      {showDemoControls && <section className="demo-switch page-shell" aria-labelledby="demo-title">
        <div>
          <Eyebrow>竞赛联调控制台</Eyebrow>
          <h2 id="demo-title">显式选择测试案例和数据来源</h2>
          <p>该控制台只在联调参数或银行审核入口下显示，不属于正式商户申请流程。</p>
        </div>
        <div className="demo-controls">
          <div className="segmented segmented--large">
            <button className={demoCase === 'normal' ? 'is-active' : ''} onClick={() => onCaseChange('normal')}>
              <span>M001</span><strong>正常授信</strong><small>审批建议 · 低风险</small>
            </button>
            <button className={demoCase === 'review' ? 'is-active' : ''} onClick={() => onCaseChange('review')}>
              <span>M005</span><strong>人工复核</strong><small>异常证据 · 压力情景</small>
            </button>
          </div>
          <div className="segmented mode-switch" aria-label="分析数据来源">
            <button className={analysisMode === 'api' ? 'is-active' : ''} onClick={() => onModeChange('api')}><strong>真实后端</strong><small>请求 FastAPI v5</small></button>
            <button className={analysisMode === 'mock' ? 'is-active' : ''} onClick={() => onModeChange('mock')}><strong>固定样例</strong><small>明确的离线演示</small></button>
          </div>
        </div>
      </section>}

      <section className="capabilities page-shell">
        <div className="section-heading">
          <Eyebrow>统一分析接口</Eyebrow>
          <h2>一套口径，三类判断</h2>
          <p>所有分数、规则与额度均由后端计算，前端只负责清晰呈现。</p>
        </div>
        <div className="capability-grid">
          {capabilities.map((item) => (
            <article className="capability-card" key={item.number}>
              <span>{item.number}</span>
              <h3>{item.title}</h3>
              <p>{item.text}</p>
              <Icon name="chevron" />
            </article>
          ))}
        </div>
      </section>
    </main>
  )
}
