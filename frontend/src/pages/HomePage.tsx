import type { DemoCase } from '../types'
import { Icon } from '../components/Icon'
import { Button, Eyebrow, InfoNote } from '../components/Ui'

interface HomePageProps {
  demoCase: DemoCase
  onCaseChange: (value: DemoCase) => void
  onStart: () => void
}

const capabilities = [
  { number: '01', title: '经营信用', text: '从稳定性、真实性、成长性与消费承接能力等维度形成可解释评分。' },
  { number: '02', title: '异常核查', text: '识别交易异常模式，输出原因码与可追溯证据，仅用于预警和人工复核。' },
  { number: '03', title: '缺口预测', text: '对未来三个月进行 P50 / P90 现金情景测算，识别流动性压力。' },
]

export function HomePage({ demoCase, onCaseChange, onStart }: HomePageProps) {
  return (
    <main>
      <section className="hero page-shell">
        <div className="hero__copy">
          <Eyebrow>小微经营 · 动态授信 MVP</Eyebrow>
          <h1>让经营数据，成为<br /><em>被看见的信用。</em></h1>
          <p className="hero__lead">
            面向小微经营者的可解释授信工作台。一次提交资料，完成经营评分、异常识别与资金缺口测算。
          </p>
          <div className="hero__actions">
            <Button icon="arrow" onClick={onStart}>开始授信测算</Button>
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

      <section className="demo-switch page-shell" aria-labelledby="demo-title">
        <div>
          <Eyebrow>联调场景</Eyebrow>
          <h2 id="demo-title">用两种固定样例检查完整状态</h2>
        </div>
        <div className="segmented segmented--large">
          <button className={demoCase === 'normal' ? 'is-active' : ''} onClick={() => onCaseChange('normal')}>
            <span>M001</span><strong>正常授信</strong><small>审批建议 · 低风险</small>
          </button>
          <button className={demoCase === 'review' ? 'is-active' : ''} onClick={() => onCaseChange('review')}>
            <span>M005</span><strong>人工复核</strong><small>异常证据 · 压力情景</small>
          </button>
        </div>
      </section>

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
