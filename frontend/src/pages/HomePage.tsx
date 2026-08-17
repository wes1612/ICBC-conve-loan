import type { DemoCasePayload } from '../types'
import { Button, Eyebrow } from '../components/Ui'

interface HomePageProps {
  demoCase: DemoCasePayload
  caseLoading: boolean
  caseError: string | null
  onRandomize: () => void
  onStart: () => void
}

const products = [
  { title: '经营快贷', tags: ['信用贷款', '随借随还'], limit: '5,000,000', rate: '3%起' },
  { title: '平台服务型授信', tags: ['消费引导', '精准评估'], limit: '5,000,000', rate: '3%起', featured: true },
  { title: '网贷通', tags: ['抵押贷款', '快速审批'], limit: '30,000,000', rate: '3%起' },
  { title: '数字供应链', tags: ['基于交易', '依链可贷'], limit: '根据订单合理确定', rate: '3%起' },
  { title: '网上质押融资', tags: ['多种押品', '额度循环'], limit: '额度循环', rate: '3%起' },
  { title: '金融资产池质押融资', tags: ['押品丰富', '随借随还'], limit: '按质押品确定', rate: '3%起' },
]

const decisionLabels = {
  APPROVE: '审批建议',
  MANUAL_REVIEW: '人工复核',
  DECLINE: '审慎拒绝',
}

const riskLabels = {
  LOW: '低风险',
  MEDIUM: '需关注',
  HIGH: '高风险',
  MANUAL_REVIEW: '人工复核',
}

export function HomePage({ demoCase, caseLoading, caseError, onRandomize, onStart }: HomePageProps) {
  return (
    <main>
      <section className="bank-landing">
        <div className="bank-topbar">
          <div className="page-shell bank-topbar__inner">
            <div className="bank-logo"><strong>ICBC</strong><span>企业网上银行</span></div>
            <nav><span>首页</span><span>金融服务</span><span>解决方案</span><span>伙伴故事</span></nav>
            <div className="bank-tools"><span>请输入关键字</span><b>95588</b><button type="button">登录</button></div>
          </div>
        </div>
        <div className="page-shell bank-hero">
          <div>
            <h1>普惠贷款</h1>
            <p>针对小微客户提供普惠贷款产品，支持实体经济，为小企业赋能。</p>
          </div>
          <Button icon="arrow" onClick={onStart} disabled={caseLoading}>开始在线测额</Button>
        </div>
      </section>

      <section className="product-section page-shell">
        <h2>普惠产品</h2>
        <div className="product-grid">
          {products.map((item) => (
            <article className={`product-card ${item.featured ? 'product-card--featured' : ''}`} key={item.title}>
              <h3>{item.title}</h3>
              <div className="product-tags">{item.tags.map((tag) => <span key={tag}>{tag}</span>)}</div>
              <div className="product-metrics">
                <div><strong>{item.limit}</strong><small>最高额度（元）</small></div>
                <div><strong>{item.rate}</strong><small>年化利率</small></div>
              </div>
              {item.featured && <p>融合平台经营数据、消费承接能力与经营真实性评估。</p>}
            </article>
          ))}
        </div>
      </section>

      <section className="demo-switch page-shell" aria-labelledby="demo-title">
        <div>
          <Eyebrow>随机演示数据</Eyebrow>
          <h2 id="demo-title">每轮从五组模拟商户中随机抽取</h2>
          <p>抽取后，申请资料、经营数据、异常检测、资金缺口和授信报告都会使用同一组记录。</p>
        </div>
        <div className={`demo-random-card ${caseLoading ? 'is-loading' : ''}`} aria-live="polite">
          <div className="demo-random-card__identity">
            <span>{caseLoading ? '抽取中' : demoCase.merchant_id}</span>
            <div>
              <strong>{caseLoading ? '正在读取模拟数据库…' : demoCase.applicant.merchant_name}</strong>
              <small>{demoCase.applicant.industry} · {demoCase.applicant.city}</small>
            </div>
          </div>
          <div className="demo-random-card__result">
            <span>{demoCase.case_label}</span>
            <strong>{decisionLabels[demoCase.expected_decision]} · {riskLabels[demoCase.expected_risk]}</strong>
            <small>{demoCase.case_description}</small>
          </div>
          <button type="button" onClick={onRandomize} disabled={caseLoading}>
            {caseLoading ? '随机抽取中…' : '换一组数据'}
          </button>
        </div>
        {caseError && <p className="demo-random-error">{caseError} 当前继续使用页面上的备用数据。</p>}
      </section>
    </main>
  )
}
