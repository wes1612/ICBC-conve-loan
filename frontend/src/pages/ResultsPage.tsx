import { useState } from 'react'
import type { DataSource, FullAnalysisResult, RiskLevel } from '../types'
import { CashGapChart, DimensionBars } from '../components/Charts'
import { Icon } from '../components/Icon'
import { AiSummaryCard } from '../components/AiSummaryCard'
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
const riskLevelLabels: Record<RiskLevel, string> = {
  LOW: '低',
  MEDIUM: '中',
  HIGH: '高',
  MANUAL_REVIEW: '人工复核',
}

function money(value: number) {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency', currency: 'CNY', maximumFractionDigits: 0,
  }).format(value)
}

function roundedLimit(value: number) {
  return Math.floor(value / 1000) * 1000
}

function riskCopy(risk: RiskLevel) {
  if (risk === 'LOW') return '当前未发现显著风险'
  if (risk === 'MEDIUM') return '存在关注项，建议补充观察'
  if (risk === 'HIGH') return '存在较高经营或流动性风险'
  return '命中人工审核门槛，不自动作出授信结论'
}

function buildRecommendationSet(data: FullAnalysisResult) {
  const score = data.score
  const review = score.review_required || data.overall_risk === 'MANUAL_REVIEW'
  const strongReputation = score.dimensions.online_reputation >= 75

  if (review) {
    return {
      strategies: [
        {
          title: '老客复购券小范围试点',
          summary: '在人工复核完成前，仅面向真实交易老客发放低强度复购券。',
          link: 'https://www.icbc.com.cn/',
          points: [
            `当前综合评分 ${score.operating_credit_score.toFixed(1)}，命中人工复核，不建议直接扩大新客补贴。`,
            data.anomaly?.rule_hits[0]?.message || '需先完成异常交易解释与经营真实性补证。',
            '适合以30天复购率、退款率和投诉率作为是否放大投放的观察指标。',
          ],
        },
        {
          title: '合作平台曝光率恢复包',
          summary: '先用平台曝光与评价修复提升交易质量，暂不进行大额补贴。',
          link: 'https://www.icbc.com.cn/',
          points: [
            `口碑维度为 ${score.dimensions.online_reputation.toFixed(1)}，需要先稳定评价和投诉表现。`,
            '通过合作平台展示经营资质、服务项目和真实评价，降低获客摩擦。',
            '待人工复核解除后，再转入定向消费券或企业员工消费导流。',
          ],
        },
      ],
      policies: [
        {
          title: '服务业经营主体贷款贴息资格预筛',
          summary: '先完成真实性和资金用途材料补充，再判断是否进入贴息申请。',
          link: 'https://jrs.mof.gov.cn/zhengcefabu/phjr/202601/t20260119_3982164.htm',
          points: [
            '政策支持经营主体贷款贴息，但逾期、不良或资料不足会影响申请。',
            `该商户当前命中 ${score.review_rules.length} 条审核规则，应先补齐纳税、开票、流水和异常说明。`,
            '如完成补件，可通过工行内部优先渠道登记贴息预审材料。',
          ],
        },
        {
          title: '地方消费券合作商户观察名单',
          summary: '暂不直接进入大规模消费券承接，先进入观察与材料准备。',
          link: 'https://www.mee.gov.cn/zcwj/gwywj/202602/t20260202_1143389.shtml',
          points: [
            '服务消费政策鼓励培育新增长点，但要求经营主体诚信合规。',
            '该商户应先降低交易异常、退款和投诉风险，避免补贴资源被误用。',
            '观察期通过后，可申请进入本地生活、社区服务或服务消费活动商户池。',
          ],
        },
      ],
    }
  }

  return {
    strategies: [
      {
        title: '定向新客消费券',
        summary: '面向门店周边一般个人账户和潜在服务消费客户投放首次消费满减券。',
        link: 'https://www.icbc.com.cn/',
        points: [
          `该商户经营评分 ${score.operating_credit_score.toFixed(1)}、等级 ${score.credit_grade}，具备承接新增订单的基础。`,
          `消费承接能力为 ${score.dimensions.capacity.toFixed(1)}，适合用新增客流验证授信资金使用效果。`,
          '工行仅在合规授权范围内完成客群匹配，不向商户披露消费者个人信息。',
        ],
      },
      {
        title: '企业员工账户定向福利券',
        summary: '将服务项目接入周边对公客户员工福利、本地生活权益和节日消费场景。',
        link: 'https://www.icbc.com.cn/',
        points: [
          '企业员工账户具备工作地点和福利需求相对明确的特点，比泛化投放更精准。',
          strongReputation ? `口碑表现 ${score.dimensions.online_reputation.toFixed(1)}，适合承接员工福利导流。` : '需同步提升评价展示，增强企业员工转化信任。',
          '消费完成后沉淀支付与结算数据，支持后续额度动态复评。',
        ],
      },
      {
        title: '工行畅销产品消费券捆绑',
        summary: '将商户服务与工行信用卡、数字人民币或本地生活活动进行组合投放。',
        link: 'https://www.icbc.com.cn/',
        points: [
          '适合美容美发、宠物服务、教育培训等服务型高频或半高频场景。',
          '通过满减、刷卡金或分期权益降低消费者首次到店门槛。',
          '以核销率、新增客户数和30日复购率判断是否扩大投放。',
        ],
      },
    ],
    policies: [
      {
        title: '服务业经营主体贷款贴息',
        summary: '推荐预筛消费领域服务业经营主体贷款贴息申请。',
        link: 'https://jrs.mof.gov.cn/zhengcefabu/phjr/202601/t20260119_3982164.htm',
        points: [
          '政策已延长至2026年12月31日，单户2026年新发放贷款贴息规模最高可达1000万元。',
          `该商户属于${score.merchant_name.includes('美发') ? '居民服务类美容美发场景' : '服务消费经营主体'}，与扩大服务消费方向匹配。`,
          `当前建议额度为 ${money(roundedLimit(score.limit.recommended_limit))}，可作为贴息预筛和资金用途说明基础。`,
        ],
      },
      {
        title: '服务消费新增长点活动商户',
        summary: '推荐申请进入本地服务消费、社区商业或生活服务活动商户池。',
        link: 'https://www.mee.gov.cn/zcwj/gwywj/202602/t20260202_1143389.shtml',
        points: [
          '政策强调优化和扩大服务供给、培育服务消费新增长点。',
          `该商户口碑维度 ${score.dimensions.online_reputation.toFixed(1)}、投诉风险维度 ${score.dimensions.complaint_risk.toFixed(1)}，具备展示给消费端的基础。`,
          '可由工行协助完成活动登记、支付核销、消费效果数据汇总。',
        ],
      },
      {
        title: '数字人民币或地方消费券合作',
        summary: '推荐作为后续消费券核销、定向发放和活动效果跟踪的候选商户。',
        link: 'https://www.icbc.com.cn/',
        points: [
          '适合需要验证新增客流、淡时段利用率和真实消费转化的门店。',
          `真实性维度 ${score.dimensions.authenticity.toFixed(1)}，可支撑活动前经营资质核验。`,
          '活动完成后可输出曝光、领取、核销、支付和复购链路报告。',
        ],
      },
    ],
  }
}

export function ResultsPage({ data, source, onRestart, onBack }: ResultsPageProps) {
  const [view, setView] = useState<'merchant' | 'reviewer'>('merchant')
  const score = data.score
  const recommendations = buildRecommendationSet(data)

  return (
    <main className="report-page report-page--dashboard">
      <div className="report-toolbar report-toolbar--dashboard page-shell">
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
        <div className="result-dashboard page-shell">
          <section className={`result-decision-card result-decision-card--${data.overall_risk.toLowerCase()}`}>
            <div>
              <h1>{score.merchant_name}</h1>
              <span>风险等级：{riskLevelLabels[data.overall_risk]}</span>
            </div>
            <strong>{decisionLabels[score.decision]}</strong>
            <small>{source === 'api' ? '综合分析已完成' : '固定联调样例'} · {data.merchant_id}</small>
          </section>

          <section className="result-score-card report-card">
            <div>
              <h2>综合评分<br />等级 {score.credit_grade}</h2>
              <p>数据置信度：{confidenceLabels[score.confidence]}</p>
            </div>
            <div className="score-ring score-ring--compact" style={{ '--score': `${score.operating_credit_score * 3.6}deg` } as React.CSSProperties}>
              <div><strong>{score.operating_credit_score.toFixed(1)}</strong><span>/ 100</span></div>
            </div>
          </section>

          <section className="result-limit-card report-card">
            <h2>建议额度</h2>
            <strong>{money(roundedLimit(score.limit.recommended_limit))}</strong>
            <p>额度将根据后续经营表现动态复评。</p>
          </section>

          <div className="result-dashboard__modules">
            <AiSummaryCard data={data} />

            <section className="merchant-rec-intro report-card">
              <h2>消费承接与政策申请推荐</h2>
              <p>工行将基于授权信息，为企业匹配消费场景、引荐入口与可申请政策。完成协议确认后，可由客户经理继续对接。</p>
            </section>

            <section className="merchant-policy-card report-card">
              <div className="card-heading"><div><h2>政策内推卡</h2></div><Icon name="bank" size={22} /></div>
              <p className="module-explanation">以下为可优先咨询的政策方向，具体资格以主管部门和银行复核为准。</p>
              <div className="compact-recommendation-list compact-recommendation-list--policy">
                {recommendations.policies.map((item) => (
                  <article key={item.title}>
                    <div><h3>{item.title}</h3><p>{item.summary}</p></div>
                    <button type="button">申请引荐</button>
                  </article>
                ))}
              </div>
            </section>

            <section className="merchant-dimension-card report-card">
              <div className="card-heading"><div><h2>经营情况评分</h2></div></div>
              <DimensionBars values={score.dimensions} />
            </section>

            <section className="merchant-consumption-card report-card">
              <div className="card-heading"><div><h2>消费承接卡</h2></div><Icon name="spark" size={22} /></div>
              <p className="module-explanation">结合企业承接能力，推荐可快速启动的消费触达方案。</p>
              <div className="compact-recommendation-list">
                {recommendations.strategies.map((item) => (
                  <article key={item.title}>
                    <div><h3>{item.title}</h3><p>{item.summary}</p></div>
                    <button type="button">签署并申请</button>
                  </article>
                ))}
              </div>
            </section>

            <section className="merchant-report-note report-card">
              <h2>经营报告已生成</h2>
              <p>评分、消费策略与政策引荐均来自本次授权数据。后续经营变化会触发动态复评。</p>
              <strong>人工客服热线：021-00000000</strong>
            </section>
          </div>
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
