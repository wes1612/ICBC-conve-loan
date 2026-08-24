import { Icon } from '../components/Icon'

const primarySteps = [
  '已生成企业经营稳定性评分',
  '已生成企业经营成长性评分',
  '已生成企业经营真实性评分',
]

export function AnalysisLoadingPage() {
  return (
    <main className="analysis-loading-page" aria-live="polite" aria-label="授信报告生成进度">
      <section className="analysis-loading-card">
        <h1>请稍后，授信报告正在生成中...</h1>
        <div className="analysis-bot assistant-smiley" aria-hidden="true">
          <Icon name="smiley" size={52} />
        </div>
        <div className="analysis-loading-steps">
          <div className="analysis-loading-steps__column">
            {primarySteps.map((label) => (
              <div className="analysis-loading-step analysis-loading-step--primary" key={label}>
                <span><Icon name="check" size={19} /></span>
                <strong>{label}...</strong>
              </div>
            ))}
            <div className="analysis-loading-step analysis-loading-step--score">
              <span><Icon name="spark" size={18} /></span>
              <strong>正在计算企业综合经营得分...</strong>
            </div>
          </div>
          <div className="analysis-loading-steps__column">
            <div className="analysis-loading-step analysis-loading-step--strategy">
              <span><Icon name="check" size={19} /></span>
              <strong>正在匹配消费策略...</strong>
            </div>
            <div className="analysis-loading-step analysis-loading-step--strategy">
              <span><Icon name="check" size={19} /></span>
              <strong>正在对接相关消费引荐入口...</strong>
            </div>
            <div className="analysis-loading-step analysis-loading-step--report">
              <span><Icon name="document" size={18} /></span>
              <strong>正在生成完整经营报告...</strong>
            </div>
          </div>
        </div>
      </section>
    </main>
  )
}
