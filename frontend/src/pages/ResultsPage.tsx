import { useState } from 'react'
import type { DataSource, FullAnalysisResult, RiskLevel } from '../types'
import { CashGapChart, DimensionBars } from '../components/Charts'
import { Icon } from '../components/Icon'
import { Button, Eyebrow, InfoNote, Metric, RiskPill } from '../components/Ui'

interface ResultsPageProps {
  data: FullAnalysisResult
  source: DataSource
  onRestart: () => void
  onBack: () => void
}

const decisionLabels = {
  APPROVE: '建议授信',
  MANUAL_REVIEW: '转人工复核',
  DECLINE: '暂不建议授信',
}

const confidenceLabels = { HIGH: '高', MEDIUM: '中', LOW: '低' }

function money(value: number) {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency', currency: 'CNY', maximumFractionDigits: 0,
  }).format(value)
}

function riskCopy(risk: RiskLevel) {
  if (risk === 'LOW') return '当前未发现显著风险'
  if (risk === 'MEDIUM') return '存在关注项，建议补充观察'
  if (risk === 'HIGH') return '存在较高经营或流动性风险'
  return '命中人工审核门槛，不自动作出授信结论'
}

export function ResultsPage({ data, source, onRestart, onBack }: ResultsPageProps) {
  const [view, setView] = useState<'merchant' | 'reviewer'>('merchant')
  const score = data.score
  const anomaly = data.anomaly
  const cash = data.cash_gap

  return (
    <main className="report-page">
      <section className={`report-hero report-hero--${data.overall_risk.toLowerCase()}`}>
        <div className="page-shell report-hero__inner">
          <div>
            <Eyebrow>综合分析结果 · {data.merchant_id}</Eyebrow>
            <h1>{score.merchant_name}</h1>
            <p>生成于 {new Intl.DateTimeFormat('zh-CN', { dateStyle: 'long', timeStyle: 'short' }).format(new Date(data.generated_at))}</p>
          </div>
          <div className="report-hero__decision">
            <RiskPill risk={data.overall_risk} />
            <h2>{decisionLabels[score.decision]}</h2>
            <p>{riskCopy(data.overall_risk)}</p>
          </div>
          <div className="report-hero__source"><i className={source === 'api' ? 'is-live' : ''} />{source === 'api' ? '真实接口响应' : '固定联调样例'} · API {data.api_version}</div>
        </div>
      </section>

      <div className="report-toolbar page-shell">
        <div className="segmented">
          <button className={view === 'merchant' ? 'is-active' : ''} onClick={() => setView('merchant')}>商户摘要</button>
          <button className={view === 'reviewer' ? 'is-active' : ''} onClick={() => setView('reviewer')}>银行审核台</button>
        </div>
        <div><Button variant="secondary" icon="download" onClick={() => window.print()}>打印结构化摘要</Button><Button variant="ghost" icon="refresh" onClick={onRestart}>切换案例</Button></div>
      </div>

      {data.data_warnings.length > 0 && (
        <div className="page-shell report-warning"><InfoNote tone="warning">{data.data_warnings.join('；')}</InfoNote></div>
      )}

      {view === 'merchant' ? (
        <div className="report-grid page-shell">
          <section className="score-card report-card">
            <div className="card-heading"><div><Eyebrow>经营信用</Eyebrow><h2>综合评分</h2></div><span>等级 {score.credit_grade}</span></div>
            <div className="score-card__body">
              <div className="score-ring" style={{ '--score': `${score.operating_credit_score * 3.6}deg` } as React.CSSProperties}>
                <div><strong>{score.operating_credit_score.toFixed(1)}</strong><span>/ 100</span></div>
              </div>
              <div className="score-summary">
                <p>评分反映经营表现与资料可信度，不等同于违约概率。</p>
                <div><Metric label="数据置信度" value={confidenceLabels[score.confidence]} /><Metric label="建议额度" value={money(score.limit.recommended_limit)} /></div>
              </div>
            </div>
            <InfoNote>真实 12 个月违约概率待历史数据校准，当前状态：<strong>{score.pd_status}</strong>。</InfoNote>
          </section>

          <section className="limit-card report-card">
            <div className="card-heading"><div><Eyebrow>授信建议</Eyebrow><h2>建议额度</h2></div><Icon name="bank" size={25} /></div>
            <strong className="big-money">{money(score.limit.recommended_limit)}</strong>
            <p>该金额由后端 v5 评分引擎生成，并非对申请金额的简单复制。</p>
            <div className="limit-factors">
              <Metric label="额度倍数" value={score.limit.score_multiplier == null ? '未适用' : `${score.limit.score_multiplier.toFixed(1)}×`} />
              <Metric label="稳定系数" value={score.limit.stability_factor.toFixed(3)} />
              <Metric label="承接系数" value={score.limit.capacity_factor.toFixed(3)} />
              <Metric label="成长加成" value={`${(score.limit.growth_bonus * 100).toFixed(0)}%`} />
            </div>
          </section>

          <section className="dimension-card report-card report-card--wide">
            <div className="card-heading"><div><Eyebrow>维度表现</Eyebrow><h2>经营画像</h2></div><span>后端输出 · 不在前端重算</span></div>
            <DimensionBars values={score.dimensions} />
          </section>

          <section className="reason-card report-card">
            <div className="card-heading"><div><Eyebrow>主要依据</Eyebrow><h2>优势与关注项</h2></div></div>
            <div className="reason-columns">
              <div><h3><Icon name="check" />经营优势</h3>{score.positive_reasons.map((reason) => <p key={reason}>{reason}</p>)}</div>
              <div><h3><Icon name="warning" />需要关注</h3>{score.negative_reasons.map((reason) => <p key={reason}>{reason}</p>)}</div>
            </div>
          </section>

          <section className="cash-summary report-card">
            <div className="card-heading"><div><Eyebrow>流动性</Eyebrow><h2>压力情景</h2></div>{cash ? <RiskPill risk={cash.risk_level as RiskLevel} /> : <span className="empty-tag">未提供</span>}</div>
            {cash ? <><strong>{money(cash.max_p90_funding_gap)}</strong><p>未来三个月最大 P90 资金缺口</p><small>{cash.first_p90_gap_month ? `首次缺口：${cash.first_p90_gap_month}` : '压力情景下未出现资金缺口'}</small></> : <EmptyModule text="未提供现金流资料，不能判断流动性风险。" />}
          </section>

          {cash && (
            <section className="cash-chart-card report-card report-card--wide">
              <div className="card-heading"><div><Eyebrow>未来三个月</Eyebrow><h2>现金余额情景</h2></div><span>资金缺口 ≠ 消费供给承接缺口</span></div>
              <CashGapChart data={cash} />
              <div className="driver-list">{cash.drivers.map((driver) => <span key={driver}><Icon name="chevron" size={15} />{driver}</span>)}</div>
            </section>
          )}

          <section className="action-plan report-card report-card--full">
            <div className="card-heading"><div><Eyebrow>经营建议</Eyebrow><h2>下一步行动</h2></div><span>基于评分原因与资金驱动</span></div>
            <div className="action-grid">
              <div><span>01</span><h3>补齐弱项证据</h3><p>{score.negative_reasons[0] || '保持现有数据完整度与主体一致性。'}</p></div>
              <div><span>02</span><h3>预留现金缓冲</h3><p>{cash?.drivers[0] || '现金流模块未提供，请补充连续 12 个月数据。'}</p></div>
              <div><span>03</span><h3>按周期复评</h3><p>经营和交易数据变化后可重新调用三个独立接口进行局部刷新。</p></div>
            </div>
            <InfoNote>自动生成 PDF 与 LLM 报告尚未实现；当前可使用浏览器打印保存结构化摘要。</InfoNote>
          </section>
        </div>
      ) : (
        <ReviewerView data={data} />
      )}

      <div className="report-footer page-shell">
        <Button variant="ghost" onClick={onBack}>返回授权页</Button>
        <p>结论用于竞赛演示与接口验收，不构成真实银行审批结果。</p>
      </div>
    </main>
  )
}

function EmptyModule({ text }: { text: string }) {
  return <div className="empty-module"><Icon name="database" /><p>{text}</p></div>
}

function ReviewerView({ data }: { data: FullAnalysisResult }) {
  const score = data.score
  const anomaly = data.anomaly
  const cash = data.cash_gap
  return (
    <div className="reviewer-layout page-shell">
      <aside className="reviewer-rail">
        <Eyebrow>审核清单</Eyebrow>
        <h2>{score.review_required ? '需要人工处理' : '无需人工复核'}</h2>
        <p>{score.review_required ? `命中 ${score.review_rules.length} 条评分审核规则` : '评分模块未命中人工审核规则。'}</p>
        <div className="rail-stats"><Metric label="经营评分" value={score.operating_credit_score.toFixed(1)} /><Metric label="异常分" value={anomaly?.anomaly_score ?? '未运行'} /><Metric label="P90 最大缺口" value={cash ? money(cash.max_p90_funding_gap) : '未运行'} /></div>
        <InfoNote tone={data.overall_risk === 'LOW' ? 'positive' : 'warning'}>{riskCopy(data.overall_risk)}</InfoNote>
      </aside>

      <div className="reviewer-content">
        <section className="report-card">
          <div className="card-heading"><div><Eyebrow>评分门控</Eyebrow><h2>人工审核规则</h2></div><span>{score.review_rules.length} 条</span></div>
          {score.review_rules.length ? <div className="rule-list">{score.review_rules.map((rule) => <div key={rule.code}><b>{rule.code}</b><span>{rule.message}</span><em className={`level level--${rule.level.toLowerCase()}`}>{rule.level}</em></div>)}</div> : <EmptyModule text="未命中评分审核规则。" />}
        </section>

        <section className="report-card">
          <div className="card-heading"><div><Eyebrow>交易异常</Eyebrow><h2>原因与证据</h2></div>{anomaly ? <RiskPill risk={anomaly.risk_level as RiskLevel} /> : <span className="empty-tag">未提供</span>}</div>
          {anomaly ? anomaly.rule_hits.length ? (
            <div className="evidence-table-wrap"><table className="evidence-table"><thead><tr><th>规则</th><th>说明</th><th>贡献</th><th>证据交易</th></tr></thead><tbody>{anomaly.rule_hits.map((hit) => <tr key={hit.code}><td><code>{hit.code}</code></td><td>{hit.message}</td><td>{hit.contribution}</td><td>{hit.evidence_transaction_ids.slice(0, 3).join('、')}{hit.evidence_transaction_ids.length > 3 ? ` 等 ${hit.evidence_transaction_ids.length} 笔` : ''}</td></tr>)}</tbody></table></div>
          ) : <EmptyModule text="当前样例未识别到交易异常。异常模块不会因此替代人工判断。" /> : <EmptyModule text="未提供交易明细，模块状态为 NOT_PROVIDED。" />}
        </section>

        <section className="report-card">
          <div className="card-heading"><div><Eyebrow>流动性核查</Eyebrow><h2>资金缺口与驱动</h2></div>{cash ? <RiskPill risk={cash.risk_level as RiskLevel} /> : <span className="empty-tag">未提供</span>}</div>
          {cash ? <><div className="reviewer-metrics"><Metric label="当前可用现金" value={money(cash.available_cash_at_snapshot)} /><Metric label="最低安全现金" value={money(cash.minimum_cash_balance)} /><Metric label="未用授信" value={money(cash.unused_credit)} /><Metric label="未用授信后需求" value={money(cash.p90_need_after_unused_credit)} /></div><CashGapChart data={cash} /></> : <EmptyModule text="未提供现金流数据，不能展示为零缺口。" />}
        </section>

        <section className="review-decision report-card">
          <div><Eyebrow>审核动作</Eyebrow><h2>记录处理意见</h2><p>原型仅展示交互，不会把意见写入数据库。</p></div>
          <div className="decision-actions"><button><Icon name="check" />建议通过</button><button><Icon name="document" />要求补件</button><button className="is-danger"><Icon name="warning" />维持人工复核</button></div>
        </section>
      </div>
    </div>
  )
}
