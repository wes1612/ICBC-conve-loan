import { useState } from 'react'
import type { AuditTrail, DataSource, EligibilityResult, FullAnalysisResult, LoanTerms, PolicyRecommendation, RepaymentCapacity, RiskLevel } from '../types'
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

function fallbackLoanTerms(data: FullAnalysisResult): LoanTerms {
  const limit = roundedLimit(data.score.limit.recommended_limit)
  return {
    requested_amount: limit,
    recommended_limit: limit,
    limit_range: [roundedLimit(limit * 0.8), limit],
    tenor_months: data.overall_decision === 'APPROVE' ? 12 : 6,
    repayment_method: data.overall_decision === 'APPROVE' ? '按月付息，到期还本；支持随借随还' : '人工复核后确定',
    is_revolving: data.overall_decision === 'APPROVE',
    drawdown_rule: data.overall_decision === 'APPROVE' ? '单笔提款不超过建议额度的30%，资金用途需匹配经营计划' : '完成补件和用途核验后放行',
    renewal_rule: '连续三个月无逾期且经营数据未恶化，可进入续贷或提额评估',
    limit_adjustment_rule: '异常交易、授权中断、P90资金缺口恶化或重大投诉触发复核',
    use_of_funds: '其他经营周转',
    use_of_funds_match: '需补充说明',
    use_of_funds_warnings: ['旧样例响应未返回资金用途规则，当前按兼容展示处理。'],
    expected_repayment_source: '经营现金流',
    repayment_source_note: '还款来源需结合现金流、订单和授权流水交叉验证。',
  }
}

function fallbackEligibility(data: FullAnalysisResult): EligibilityResult {
  return {
    status: data.score.review_required ? 'MANUAL_REVIEW' : 'ELIGIBLE',
    conclusion: data.score.review_required ? '符合客群但需人工审核' : '符合试点客群',
    pilot_industry: true,
    reasons: [`经营信用等级：${data.score.credit_grade}`, `数据置信度：${data.score.confidence}`],
    warnings: data.score.review_required ? ['命中评分人工审核规则'] : [],
  }
}

function fallbackRepaymentCapacity(data: FullAnalysisResult): RepaymentCapacity {
  const cash = data.cash_gap
  return {
    conclusion: data.score.review_required ? '偿债能力需人工复核' : '经营现金流对拟授信具备基础覆盖能力',
    confidence: data.score.confidence,
    monthly_operating_inflow: cash?.forecasts[0]?.p50_operating_inflow ?? null,
    monthly_operating_outflow: cash?.forecasts[0]?.p50_operating_outflow ?? null,
    fixed_cost_coverage: null,
    p90_funding_gap: cash?.max_p90_funding_gap ?? null,
    debt_pressure_level: cash?.risk_level ?? 'NOT_PROVIDED',
    refund_complaint_pressure: '由退款率、投诉风险和异常交易规则共同观察',
    evidence: [`经营信用分 ${data.score.operating_credit_score.toFixed(1)}`, `风险带 ${data.score.risk_band}`],
  }
}

function fallbackAuditTrail(data: FullAnalysisResult): AuditTrail {
  return {
    consent_version: 'consent_v1_2026_08',
    consent_timestamp: null,
    authorized_sources: [],
    material_hashes: {},
    material_ids: data.material_evidence.map((item) => item.material_id),
    score_version: data.score.score_version,
    rules_version: data.score.profile,
    model_version: 'scorecard_v5 + anomaly_hybrid_v1 + cash_gap_baseline_v1',
    generated_at: data.generated_at,
    ai_used: false,
  }
}

function formatDate(value: string | null) {
  if (!value) return '待记录'
  return new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}


function buildPolicyRecommendationSet(data: FullAnalysisResult) {
  const policies = data.policy_recommendations ?? []
  if (!policies.length) return null
  const reviewed = policies.filter((item) => item.status === 'ACTIVE')
  const candidate = policies.filter((item) => item.status !== 'ACTIVE')
  const toCard = (item: PolicyRecommendation) => ({
    title: item.policy_name,
    summary: `${item.policy_level} · ${item.support_method} · ${item.match_level}`,
    link: item.source_url || 'https://www.icbc.com.cn/',
    points: [
      item.reason,
      item.support_standard,
      item.warnings[0] || `材料：${item.required_materials.slice(0, 3).join('、')}`,
    ],
  })
  const bankPoints = policies.flatMap((item) => item.bank_actions).slice(0, 6)
  return {
    strategies: [
      {
        title: '工行政策协同消费引介方案',
        summary: '把政策申请、消费活动和支付核销数据纳入同一行动清单。',
        link: 'https://www.icbc.com.cn/',
        points: bankPoints.length ? bankPoints : ['协助核验政策条件', '组织消费券或平台曝光试点', '把核销和复购数据纳入贷后监控'],
      },
      ...policies.flatMap((item) => item.consumer_introduction).slice(0, 2).map((point, index) => ({
        title: index === 0 ? '消费场景承接' : '支付与核销闭环',
        summary: '由政策标签与商户经营画像共同触发。',
        link: 'https://www.icbc.com.cn/',
        points: [point, '活动数据会回流至后续额度动态复评。', '不向商户披露消费者个人敏感信息。'],
      })),
    ],
    policies: [...reviewed, ...candidate].slice(0, 4).map(toCard),
  }
}
function buildRecommendationSet(data: FullAnalysisResult) {
  const score = data.score
  const loanTerms = data.loan_terms ?? fallbackLoanTerms(data)
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
            `当前资金用途为“${loanTerms.use_of_funds}”，需先完成用途证明与还款来源解释。`,
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
          `该商户资金用途为“${loanTerms.use_of_funds}”，与服务消费经营主体融资场景可形成材料闭环。`,
          `当前授信方案建议额度为 ${money(loanTerms.recommended_limit)}，可作为贴息预筛和资金用途说明基础。`,
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
  const loanTerms = data.loan_terms ?? fallbackLoanTerms(data)
  const repaymentCapacity = data.repayment_capacity ?? fallbackRepaymentCapacity(data)
  const recommendations = buildPolicyRecommendationSet(data) ?? buildRecommendationSet(data)

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
        <div className="report-grid report-grid--final page-shell">
          <AiSummaryCard data={data} />

          <section className="score-card report-card">
            <div className="card-heading"><div><h2>综合评分：等级 {score.credit_grade}</h2></div></div>
            <div className="score-card__body">
              <div className="score-ring" style={{ '--score': `${score.operating_credit_score * 3.6}deg` } as React.CSSProperties}>
                <div><strong>{score.operating_credit_score.toFixed(1)}</strong><span>/ 100</span></div>
              </div>
              <div className="score-summary">
                <p>评分反映经营表现与资料可信度，不等同于违约概率。</p>
                <div>
                  <Metric label="数据置信度" value={confidenceLabels[score.confidence]} />
                  <Metric label="资金用途" value={loanTerms.use_of_funds} />
                </div>
              </div>
            </div>
          </section>

          <section className="loan-product-card report-card">
            <div className="card-heading"><div><h2>授信方案</h2></div><Icon name="bank" size={25} /></div>
            <strong className="big-money">{money(loanTerms.recommended_limit)}</strong>
            <div className="loan-product-grid">
              <Metric label="额度区间" value={`${money(loanTerms.limit_range[0])} - ${money(loanTerms.limit_range[1])}`} />
              <Metric label="建议期限" value={loanTerms.tenor_months > 0 ? `${loanTerms.tenor_months} 个月` : '暂不配置'} />
              <Metric label="循环额度" value={loanTerms.is_revolving ? '支持' : '暂不支持'} />
            </div>
            <div className="loan-detail-list">
              <div><span>还款方式</span><strong>{loanTerms.repayment_method}</strong></div>
              <div><span>提款规则</span><strong>{loanTerms.drawdown_rule}</strong></div>
              <div><span>用途匹配</span><strong>{loanTerms.use_of_funds_match}</strong></div>
            </div>
          </section>

          <section className="dimension-card report-card report-card--wide">
            <div className="card-heading"><div><h2>经营画像</h2></div></div>
            <DimensionBars values={score.dimensions} />
          </section>

          <section className="repayment-card report-card">
            <div className="card-heading"><div><h2>还款能力</h2></div><span>{confidenceLabels[repaymentCapacity.confidence]}</span></div>
            <p>{repaymentCapacity.conclusion}</p>
            <div className="loan-product-grid loan-product-grid--two">
              <Metric label="月均经营流入" value={repaymentCapacity.monthly_operating_inflow == null ? '未运行' : money(repaymentCapacity.monthly_operating_inflow)} />
              <Metric label="P90 最大缺口" value={repaymentCapacity.p90_funding_gap == null ? '未运行' : money(repaymentCapacity.p90_funding_gap)} />
            </div>
            <ul className="mini-list">{repaymentCapacity.evidence.map((item) => <li key={item}>{item}</li>)}</ul>
          </section>

          <section className="recommendation-intro report-card report-card--full">
            <h2>消费承接与政策申请推荐</h2>
            <p>本栏目给出部分 ICBC 可以为贵司提供的消费场景引介和推荐的政策申请。工商银行主要提供的消费场景包括：①一般个人账户、企业员工账户定向消费券发放；②合作平台曝光率增加；③工商银行畅销产品消费券捆绑。</p>
            <p>推荐的政策申请，即工商银行根据贵司情况推荐贵司申请的相关政府消费政策。贵司如有需要，可以通过工行内部优先渠道申请。</p>
            <p>如您需要申请以上政策或消费场景，请点击对应按钮签署协议。签署协议完成后，后台会自动为您登记信息、进入申请流程。如有需要，会有人工客服通过联系人手机号码联系您。</p>
          </section>

          <section className="recommendation-card report-card report-card--full">
            <div className="card-heading"><div><h2>消费承接卡</h2></div></div>
            <div className="recommendation-stack">
              {recommendations.strategies.map((item) => (
                <article key={item.title} className="dark-rec-card">
                  <div>
                    <h3>{item.title}</h3>
                    <p>{item.summary}</p>
                    <a href={item.link} target="_blank" rel="noreferrer">{item.link}</a>
                  </div>
                  <ul>{item.points.map((point) => <li key={point}>{point}</li>)}</ul>
                  <button type="button">签署协议并申请</button>
                </article>
              ))}
            </div>
          </section>

          <section className="recommendation-card report-card report-card--full">
            <div className="card-heading"><div><h2>推荐政策卡</h2></div></div>
            <div className="recommendation-stack">
              {recommendations.policies.map((item) => (
                <article key={item.title} className="dark-rec-card dark-rec-card--policy">
                  <div>
                    <h3>{item.title}</h3>
                    <p>{item.summary}</p>
                    <a href={item.link} target="_blank" rel="noreferrer">{item.link}</a>
                  </div>
                  <ul>{item.points.map((point) => <li key={point}>{point}</li>)}</ul>
                  <button type="button">签署协议并申请</button>
                </article>
              ))}
            </div>
          </section>

          <section className="report-closing-note report-card report-card--full">
            <p>长期授信与消费引导服务会根据贵司实时经营情况动态调整，以持续跟进贵司贷后情况，达到全生命周期服务与支持的效果。您可以在贷后或申请消费政策后随时登录本平台，查看最新经营分析与授信额度。</p>
            <p>更多分析结果与详尽信息，请下载结构化摘要查看。如有疑问，请咨询工小信或人工客服。</p>
            <strong>人工客服热线：021-00000000</strong>
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
  const eligibility = data.eligibility ?? fallbackEligibility(data)
  const loanTerms = data.loan_terms ?? fallbackLoanTerms(data)
  const repaymentCapacity = data.repayment_capacity ?? fallbackRepaymentCapacity(data)
  const auditTrail = data.audit_trail ?? fallbackAuditTrail(data)
  return (
    <div className="reviewer-layout page-shell">
      <aside className="reviewer-rail">
        <Eyebrow>审核清单</Eyebrow>
        <h2>{score.review_required ? '需要人工处理' : '无需人工复核'}</h2>
        <p>{score.review_required ? `命中 ${score.review_rules.length} 条评分审核规则` : '评分模块未命中人工审核规则。'}</p>
        <div className="rail-stats"><Metric label="经营评分" value={score.operating_credit_score.toFixed(1)} /><Metric label="授信方案" value={money(loanTerms.recommended_limit)} /><Metric label="P90 最大缺口" value={cash ? money(cash.max_p90_funding_gap) : '未运行'} /></div>
        <InfoNote tone={data.overall_risk === 'LOW' ? 'positive' : 'warning'}>{riskCopy(data.overall_risk)}</InfoNote>
      </aside>

      <div className="reviewer-content">
        <section className="report-card">
          <div className="card-heading"><div><Eyebrow>准入判断</Eyebrow><h2>{eligibility.conclusion}</h2></div><span>{eligibility.status}</span></div>
          <div className="review-grid">
            <Metric label="试点行业" value={eligibility.pilot_industry ? '符合' : '不符合'} />
            <Metric label="资金用途" value={loanTerms.use_of_funds} />
            <Metric label="用途匹配" value={loanTerms.use_of_funds_match} />
          </div>
          <ul className="mini-list">{eligibility.reasons.map((item) => <li key={item}>{item}</li>)}</ul>
          {eligibility.warnings.length > 0 && <ul className="loan-warning-list">{eligibility.warnings.map((item) => <li key={item}>{item}</li>)}</ul>}
        </section>

        <section className="report-card">
          <div className="card-heading"><div><Eyebrow>评分门控</Eyebrow><h2>人工审核规则</h2></div><span>{score.review_rules.length} 条</span></div>
          {score.review_rules.length ? <div className="rule-list">{score.review_rules.map((rule) => <div key={rule.code}><b>{rule.code}</b><span>{rule.message}</span><em className={`level level--${rule.level.toLowerCase()}`}>{rule.level}</em></div>)}</div> : <EmptyModule text="未命中评分审核规则。" />}
        </section>

        <section className="report-card">
          <div className="card-heading"><div><Eyebrow>偿债能力</Eyebrow><h2>{repaymentCapacity.conclusion}</h2></div><span>{confidenceLabels[repaymentCapacity.confidence]}</span></div>
          <div className="reviewer-metrics">
            <Metric label="月均经营流入" value={repaymentCapacity.monthly_operating_inflow == null ? '未运行' : money(repaymentCapacity.monthly_operating_inflow)} />
            <Metric label="月均经营流出" value={repaymentCapacity.monthly_operating_outflow == null ? '未运行' : money(repaymentCapacity.monthly_operating_outflow)} />
            <Metric label="固定成本覆盖" value={repaymentCapacity.fixed_cost_coverage == null ? '未运行' : `${repaymentCapacity.fixed_cost_coverage}x`} />
            <Metric label="P90 最大缺口" value={repaymentCapacity.p90_funding_gap == null ? '未运行' : money(repaymentCapacity.p90_funding_gap)} />
          </div>
          <ul className="mini-list">{repaymentCapacity.evidence.map((item) => <li key={item}>{item}</li>)}</ul>
        </section>

        <section className="report-card">
          <div className="card-heading"><div><Eyebrow>授信产品参数</Eyebrow><h2>提款、续贷与调整</h2></div></div>
          <div className="loan-detail-list">
            <div><span>额度区间</span><strong>{money(loanTerms.limit_range[0])} - {money(loanTerms.limit_range[1])}</strong></div>
            <div><span>还款来源</span><strong>{loanTerms.expected_repayment_source}；{loanTerms.repayment_source_note}</strong></div>
            <div><span>续贷规则</span><strong>{loanTerms.renewal_rule}</strong></div>
            <div><span>额度调整</span><strong>{loanTerms.limit_adjustment_rule}</strong></div>
          </div>
          {loanTerms.use_of_funds_warnings.length > 0 && <ul className="loan-warning-list">{loanTerms.use_of_funds_warnings.map((item) => <li key={item}>{item}</li>)}</ul>}
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

        <section className="report-card">
          <div className="card-heading"><div><Eyebrow>合规审计</Eyebrow><h2>授权与版本留痕</h2></div><span>{auditTrail.ai_used ? '含AI解释' : '规则链路'}</span></div>
          <div className="audit-grid">
            <div><span>授权版本</span><strong>{auditTrail.consent_version}</strong></div>
            <div><span>授权时间</span><strong>{formatDate(auditTrail.consent_timestamp)}</strong></div>
            <div><span>评分版本</span><strong>{auditTrail.score_version}</strong></div>
            <div><span>规则 Profile</span><strong>{auditTrail.rules_version}</strong></div>
            <div><span>材料数量</span><strong>{auditTrail.material_ids.length} 份</strong></div>
            <div><span>授权来源</span><strong>{auditTrail.authorized_sources.length ? auditTrail.authorized_sources.join('、') : '旧样例未返回'}</strong></div>
          </div>
          <p className="audit-model">{auditTrail.model_version}</p>
        </section>

        <section className="review-decision report-card">
          <div><Eyebrow>审核动作</Eyebrow><h2>记录处理意见</h2><p>原型仅展示交互，不会把意见写入数据库。</p></div>
          <div className="decision-actions"><button><Icon name="check" />建议通过</button><button><Icon name="document" />要求补件</button><button className="is-danger"><Icon name="warning" />维持人工复核</button></div>
        </section>
      </div>
    </div>
  )
}