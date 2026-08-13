import type { DemoCase } from '../types'
import { Button, Eyebrow } from '../components/Ui'

interface HomePageProps {
  demoCase: DemoCase
  onCaseChange: (value: DemoCase) => void
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

export function HomePage({ demoCase, onCaseChange, onStart }: HomePageProps) {
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
          <Button icon="arrow" onClick={onStart}>开始在线测额</Button>
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
    </main>
  )
}
