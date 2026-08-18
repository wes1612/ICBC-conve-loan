import { useCallback, useEffect, useMemo, useState, type FormEvent } from 'react'
import {
  advancePostLoanMonth,
  decidePostLoanReview,
  describeApiError,
  getPostLoanTimeline,
  renewPostLoanSource,
  resetPostLoanTimeline,
  submitPostLoanSupplement,
} from '../api'
import { Icon } from '../components/Icon'
import { Button, Eyebrow, InfoNote } from '../components/Ui'
import type {
  DemoMerchantId,
  PostLoanAction,
  PostLoanSnapshot,
  PostLoanTimeline,
} from '../types'

const merchantOptions: Array<{ id: DemoMerchantId; label: string }> = [
  { id: 'M001', label: 'M001 · 稳定经营' },
  { id: 'M002', label: 'M002 · 快速成长' },
  { id: 'M003', label: 'M003 · 经营恶化' },
  { id: 'M004', label: 'M004 · 数据缺失' },
  { id: 'M005', label: 'M005 · 异常交易' },
]

const actionLabels: Record<PostLoanAction, string> = {
  INCREASE: '建议提额',
  MAINTAIN: '维持额度',
  DECREASE: '建议降额',
  FREEZE: '冻结新增提款',
  MANUAL_REVIEW: '人工复核',
}

const reviewStatusLabels = {
  AUTO_APPLIED: '规则已执行',
  PENDING_REVIEW: '等待银行审核',
  APPROVED: '银行已批准',
  REJECTED: '本期维持原额度',
}

const sourceTypeLabels = {
  BANK_INTERNAL_SIMULATED: '银行内部模拟',
  PLATFORM_AUTHORIZED_SIMULATED: '授权平台模拟',
  MERCHANT_SUBMITTED_SIMULATED: '商户申报模拟',
  MANUAL_VERIFIED_SIMULATED: '人工核验模拟',
}

const authLabels = {
  ACTIVE: '授权有效',
  EXPIRED: '授权已到期',
  REVOKED: '授权已撤销',
  NOT_REQUIRED: '银行自有/无需授权',
}

const categoryLabels = {
  OFF_BANK_STATEMENT: '他行流水',
  CONTRACT: '经营合同',
  PURPOSE_PROOF: '资金用途证明',
  EXPLANATION: '异常情况说明',
}

function money(value: number) {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    maximumFractionDigits: 0,
  }).format(value)
}

function monthLabel(value: string) {
  const date = new Date(`${value.slice(0, 10)}T00:00:00`)
  return `${date.getFullYear()}年${date.getMonth() + 1}月`
}

function dateTimeLabel(value: string | null) {
  if (!value) return '尚未同步'
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit',
  }).format(new Date(value))
}

function linePoints(values: number[], width: number, height: number, padding = 18) {
  if (!values.length) return ''
  const minimum = Math.min(...values)
  const maximum = Math.max(...values)
  const range = maximum - minimum || 1
  return values.map((value, index) => {
    const x = padding + index * ((width - padding * 2) / Math.max(1, values.length - 1))
    const y = height - padding - ((value - minimum) / range) * (height - padding * 2)
    return `${x.toFixed(1)},${y.toFixed(1)}`
  }).join(' ')
}

function TrendChart({ snapshots }: { snapshots: PostLoanSnapshot[] }) {
  const width = 720
  const height = 220
  const scores = snapshots.map((item) => item.models.operating_credit_score)
  const limits = snapshots.map((item) => item.review.current_limit / 10_000)
  const scorePoints = linePoints(scores, width, height)
  const limitPoints = linePoints(limits, width, height)
  return (
    <div className="postloan-chart">
      <div className="postloan-chart__legend">
        <span><i className="is-score" />经营信用评分</span>
        <span><i className="is-limit" />生效额度（万元）</span>
      </div>
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="评分与额度月度变化曲线">
        {[0.2, 0.4, 0.6, 0.8].map((ratio) => (
          <line key={ratio} x1="18" x2={width - 18} y1={height * ratio} y2={height * ratio} className="postloan-chart__grid" />
        ))}
        <polyline points={scorePoints} className="postloan-chart__line postloan-chart__line--score" />
        <polyline points={limitPoints} className="postloan-chart__line postloan-chart__line--limit" />
        {snapshots.map((item, index) => {
          const [x, y] = scorePoints.split(' ')[index].split(',')
          return <circle key={item.month} cx={x} cy={y} r="4" className="postloan-chart__dot" />
        })}
      </svg>
      <div className="postloan-chart__months">
        {snapshots.map((item) => <span key={item.month}>{monthLabel(item.month).replace('年', '/').replace('月', '')}</span>)}
      </div>
    </div>
  )
}

interface PostLoanPageProps {
  initialMerchantId: DemoMerchantId
}

export function PostLoanPage({ initialMerchantId }: PostLoanPageProps) {
  const [merchantId, setMerchantId] = useState<DemoMerchantId>(initialMerchantId)
  const [timeline, setTimeline] = useState<PostLoanTimeline | null>(null)
  const [view, setView] = useState<'bank' | 'merchant'>('bank')
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [category, setCategory] = useState<keyof typeof categoryLabels>('EXPLANATION')
  const [description, setDescription] = useState('')
  const [file, setFile] = useState<File | null>(null)

  const load = useCallback(async (id: DemoMerchantId) => {
    setLoading(true)
    setError(null)
    try {
      setTimeline(await getPostLoanTimeline(id))
    } catch (nextError) {
      setError(describeApiError(nextError))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { void load(merchantId) }, [load, merchantId])

  const runMutation = async (mutation: () => Promise<PostLoanTimeline>) => {
    if (busy) return
    setBusy(true)
    setError(null)
    try {
      setTimeline(await mutation())
    } catch (nextError) {
      setError(describeApiError(nextError))
    } finally {
      setBusy(false)
    }
  }

  const current = timeline?.snapshots[timeline.snapshots.length - 1]
  const pendingReview = timeline?.current_review.status === 'PENDING_REVIEW'
  const latestSourceWarning = useMemo(
    () => timeline?.source_statuses.filter((source) => ['EXPIRED', 'REVOKED'].includes(source.authorization_status)) || [],
    [timeline],
  )

  const submitSupplement = async (event: FormEvent) => {
    event.preventDefault()
    if (!timeline || description.trim().length < 5) return
    await runMutation(() => submitPostLoanSupplement(timeline.merchant_id, {
      category,
      description: description.trim(),
      file_name: file?.name || null,
    }))
    setDescription('')
    setFile(null)
  }

  if (loading && !timeline) {
    return <main className="postloan-page"><div className="page-shell postloan-loading"><i />正在生成贷后月度快照…</div></main>
  }

  if (!timeline || !current) {
    return (
      <main className="postloan-page">
        <div className="page-shell postloan-empty">
          <Icon name="warning" size={28} />
          <h1>贷后监测数据暂不可用</h1>
          <p>{error || '请确认后端服务已经启动。'}</p>
          <Button onClick={() => void load(merchantId)}>重新加载</Button>
        </div>
      </main>
    )
  }

  const review = timeline.current_review
  return (
    <main className="postloan-page">
      <section className={`postloan-hero postloan-hero--${review.alert_level.toLowerCase()}`}>
        <div className="page-shell postloan-hero__inner">
          <div>
            <Eyebrow>贷后全周期动态授信 · 竞赛模拟</Eyebrow>
            <h1>{timeline.merchant_name}</h1>
            <p>{timeline.scenario_name}：{timeline.scenario_description}</p>
            <div className="postloan-hero__progress">
              <span>贷后第 {timeline.current_month_index} / {timeline.total_months} 月</span>
              <i><b style={{ width: `${timeline.current_month_index / timeline.total_months * 100}%` }} /></i>
              <span>{monthLabel(timeline.as_of_month)}</span>
            </div>
          </div>
          <div className="postloan-hero__controls">
            <label>
              <span>演示商户轨迹</span>
              <select value={merchantId} onChange={(event) => setMerchantId(event.target.value as DemoMerchantId)} disabled={busy}>
                {merchantOptions.map((option) => <option value={option.id} key={option.id}>{option.label}</option>)}
              </select>
            </label>
            <div>
              <Button variant="secondary" icon="refresh" disabled={busy} onClick={() => void runMutation(() => resetPostLoanTimeline(merchantId))}>重置轨迹</Button>
              <Button icon="arrow" disabled={busy || timeline.current_month_index >= 12} onClick={() => void runMutation(() => advancePostLoanMonth(merchantId))}>推进到下个月</Button>
            </div>
          </div>
        </div>
      </section>

      <div className="postloan-toolbar page-shell">
        <div className="segmented">
          <button className={view === 'bank' ? 'is-active' : ''} onClick={() => setView('bank')}>银行贷后监测台</button>
          <button className={view === 'merchant' ? 'is-active' : ''} onClick={() => setView('merchant')}>商户补充端</button>
        </div>
        <span><i className="is-live" />三套分析引擎已完成本月复评</span>
      </div>

      {error && <div className="page-shell postloan-error"><InfoNote tone="warning">{error}</InfoNote></div>}

      {view === 'bank' ? (
        <div className="page-shell postloan-dashboard">
          <section className="postloan-kpis">
            <article><span>当前生效额度</span><strong>{money(timeline.loan_account.current_limit)}</strong><small>初始 {money(timeline.loan_account.initial_limit)}</small></article>
            <article><span>未偿本金</span><strong>{money(timeline.loan_account.outstanding_principal)}</strong><small>使用率 {(current.operating.limit_utilization * 100).toFixed(1)}%</small></article>
            <article className={timeline.loan_account.status === 'FROZEN' ? 'is-danger' : ''}><span>可用额度</span><strong>{money(timeline.loan_account.available_limit)}</strong><small>{timeline.loan_account.status === 'FROZEN' ? '新增提款已冻结' : '账户状态正常'}</small></article>
            <article><span>经营信用评分</span><strong>{current.models.operating_credit_score.toFixed(1)}</strong><small>等级 {current.models.credit_grade} · 置信度 {current.models.confidence}</small></article>
          </section>

          <section className={`postloan-decision postloan-card postloan-decision--${review.action.toLowerCase()}`}>
            <div className="postloan-decision__title">
              <span><Icon name={review.action === 'FREEZE' ? 'lock' : review.action === 'INCREASE' ? 'spark' : 'shield'} size={24} /></span>
              <div><Eyebrow>本月动态额度建议</Eyebrow><h2>{actionLabels[review.action]}</h2></div>
              <em>{reviewStatusLabels[review.status]}</em>
            </div>
            <div className="postloan-decision__amounts">
              <div><span>当前额度</span><strong>{money(review.current_limit)}</strong></div>
              <Icon name="arrow" size={24} />
              <div><span>模型候选额度</span><strong>{money(review.candidate_limit)}</strong></div>
              <Icon name="arrow" size={24} />
              <div className="is-proposed"><span>政策建议额度</span><strong>{money(review.proposed_limit)}</strong></div>
            </div>
            <ul>{review.reasons.map((reason) => <li key={reason}><Icon name="check" size={15} />{reason}</li>)}</ul>
            <div className="postloan-reason-codes">{review.reason_codes.map((code) => <code key={code}>{code}</code>)}</div>
            {pendingReview && (
              <div className="postloan-decision__actions">
                <Button disabled={busy} onClick={() => void runMutation(() => decidePostLoanReview(review.review_id, 'APPROVE', review.proposed_limit))}>批准系统建议</Button>
                <Button variant="secondary" disabled={busy} onClick={() => void runMutation(() => decidePostLoanReview(review.review_id, 'MAINTAIN'))}>维持原额度</Button>
                <Button variant="ghost" disabled={busy} onClick={() => void runMutation(() => decidePostLoanReview(review.review_id, 'ESCALATE'))}>升级人工核查</Button>
              </div>
            )}
          </section>

          <div className="postloan-two-column">
            <section className="postloan-card">
              <div className="postloan-section-title"><div><Eyebrow>月度变化</Eyebrow><h2>评分与生效额度轨迹</h2></div><span>{timeline.snapshots.length} 期快照</span></div>
              <TrendChart snapshots={timeline.snapshots} />
            </section>
            <section className="postloan-card postloan-models">
              <div className="postloan-section-title"><div><Eyebrow>本月模型输出</Eyebrow><h2>三引擎联合复评</h2></div></div>
              <div><span>经营评分</span><strong>{current.models.operating_credit_score.toFixed(1)}</strong><small>{current.models.score_model_version}</small></div>
              <div><span>异常交易</span><strong>{current.models.anomaly_score}</strong><small>{current.models.anomaly_risk} · {current.models.anomaly_model_version}</small></div>
              <div><span>P90 最大资金缺口</span><strong>{money(current.models.max_p90_funding_gap)}</strong><small>{current.models.cash_gap_risk} · {current.models.cash_gap_model_version}</small></div>
              <p>三套引擎负责计算证据，动态额度状态机负责政策约束；LLM 不参与评分和额度决策。</p>
            </section>
          </div>

          <section className="postloan-card">
            <div className="postloan-section-title"><div><Eyebrow>数据证据链</Eyebrow><h2>来源、授权与同步状态</h2></div><span>自动采集为主 · 商户补充为辅</span></div>
            <div className="postloan-sources">
              {timeline.source_statuses.map((source) => (
                <article className={source.quality_status === 'MISSING' ? 'has-warning' : ''} key={source.source_id}>
                  <div><span><Icon name={source.source_type === 'BANK_INTERNAL_SIMULATED' ? 'bank' : source.source_type === 'PLATFORM_AUTHORIZED_SIMULATED' ? 'database' : source.source_type === 'MERCHANT_SUBMITTED_SIMULATED' ? 'upload' : 'shield'} size={19} /></span><div><strong>{source.display_name}</strong><small>{sourceTypeLabels[source.source_type]}</small></div></div>
                  <em>{authLabels[source.authorization_status]}</em>
                  <p>{source.scopes.join(' · ')}</p>
                  <footer><span>最近同步 {dateTimeLabel(source.last_synced_at)}</span><span>{source.record_count} 条</span></footer>
                  {['EXPIRED', 'REVOKED'].includes(source.authorization_status) && (
                    <button disabled={busy} onClick={() => void runMutation(() => renewPostLoanSource(merchantId, source.source_id))}>模拟续期授权</button>
                  )}
                </article>
              ))}
            </div>
          </section>

          <section className="postloan-card">
            <div className="postloan-section-title"><div><Eyebrow>可追溯历史</Eyebrow><h2>月度快照与额度动作</h2></div></div>
            <div className="postloan-table-wrap">
              <table className="postloan-table">
                <thead><tr><th>月份</th><th>经营流水</th><th>还款</th><th>评分</th><th>异常/缺口</th><th>额度动作</th><th>审核状态</th></tr></thead>
                <tbody>{[...timeline.snapshots].reverse().map((snapshot) => (
                  <tr key={snapshot.month}>
                    <td><strong>{monthLabel(snapshot.month)}</strong><small>第 {snapshot.month_index} 月</small></td>
                    <td>{money(snapshot.operating.receipts)}<small className={(snapshot.operating.receipt_mom_growth || 0) < 0 ? 'is-negative' : 'is-positive'}>{((snapshot.operating.receipt_mom_growth || 0) * 100).toFixed(1)}%</small></td>
                    <td>{snapshot.repayment.on_time ? '按期' : `逾期 ${snapshot.repayment.days_past_due} 天`}</td>
                    <td>{snapshot.models.operating_credit_score.toFixed(1)} · {snapshot.models.credit_grade}</td>
                    <td>{snapshot.models.anomaly_risk} / {snapshot.models.cash_gap_risk}</td>
                    <td><span className={`postloan-action postloan-action--${snapshot.review.action.toLowerCase()}`}>{actionLabels[snapshot.review.action]}</span><small>{money(snapshot.review.proposed_limit)}</small></td>
                    <td>{reviewStatusLabels[snapshot.review.status]}</td>
                  </tr>
                ))}</tbody>
              </table>
            </div>
          </section>

          <div className="postloan-two-column postloan-two-column--bottom">
            <section className="postloan-card">
              <div className="postloan-section-title"><div><Eyebrow>风险事件</Eyebrow><h2>贷后预警时间线</h2></div><span>{timeline.alerts.length} 项</span></div>
              {timeline.alerts.length ? <div className="postloan-alerts">{[...timeline.alerts].reverse().map((alert) => (
                <article key={alert.alert_id} className={`postloan-alert postloan-alert--${alert.level.toLowerCase()}`}><i /><div><span>{dateTimeLabel(alert.occurred_at)}</span><strong>{alert.title}</strong><p>{alert.description}</p><code>{alert.evidence_refs.join(' · ')}</code></div></article>
              ))}</div> : <div className="postloan-no-alert"><Icon name="shield" size={28} /><strong>当前没有中高风险预警</strong><span>系统仍会按月持续生成特征快照。</span></div>}
            </section>
            <section className="postloan-card postloan-policy">
              <div className="postloan-section-title"><div><Eyebrow>风险护栏</Eyebrow><h2>竞赛模拟政策说明</h2></div></div>
              <ul>{timeline.policy_notes.map((note) => <li key={note}><Icon name="shield" size={17} />{note}</li>)}</ul>
            </section>
          </div>
        </div>
      ) : (
        <div className="page-shell postloan-merchant">
          <section className="postloan-card postloan-merchant__intro">
            <div><Eyebrow>商户贷后服务</Eyebrow><h2>只需补充银行和授权平台无法自动取得的信息</h2><p>还款、贷款余额和工行回款账户由系统自动获取；他行流水、合同、资金用途证明和异常说明由商户按需补充。</p></div>
            <Icon name="upload" size={44} />
          </section>
          {latestSourceWarning.length > 0 && <InfoNote tone="warning">{latestSourceWarning.map((source) => source.display_name).join('、')}授权异常，请先在银行监测台续期，或提交替代材料。</InfoNote>}
          <div className="postloan-two-column">
            <form className="postloan-card postloan-submit" onSubmit={submitSupplement}>
              <div className="postloan-section-title"><div><Eyebrow>补充证据</Eyebrow><h2>提交材料或异常说明</h2></div></div>
              <label><span>材料类型</span><select value={category} onChange={(event) => setCategory(event.target.value as keyof typeof categoryLabels)}>{Object.entries(categoryLabels).map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
              <label><span>情况说明</span><textarea value={description} onChange={(event) => setDescription(event.target.value)} placeholder="说明材料对应月份、用途或需要解释的异常原因…" maxLength={500} /></label>
              <label className="postloan-file"><input type="file" accept=".pdf,.png,.jpg,.jpeg,.xlsx,.xls,.csv" onChange={(event) => setFile(event.target.files?.[0] || null)} /><Icon name="upload" size={20} /><span>{file ? file.name : '选择一份模拟证明文件（可选）'}</span></label>
              <Button disabled={busy || description.trim().length < 5} icon="arrow">提交并等待核验</Button>
              <small>商户申报不会直接改变额度，需与银行或平台数据交叉核验。</small>
            </form>
            <section className="postloan-card">
              <div className="postloan-section-title"><div><Eyebrow>提交记录</Eyebrow><h2>补充材料处理进度</h2></div><span>{timeline.submissions.length} 份</span></div>
              {timeline.submissions.length ? <div className="postloan-submissions">{[...timeline.submissions].reverse().map((submission) => (
                <article key={submission.submission_id}><span><Icon name="document" size={19} /></span><div><strong>{categoryLabels[submission.category]}</strong><p>{submission.description}</p><small>{submission.file_name || '仅提交文字说明'} · {dateTimeLabel(submission.submitted_at)}</small></div><em>{submission.verification_status === 'PENDING' ? '待核验' : submission.verification_status}</em></article>
              ))}</div> : <div className="postloan-no-alert"><Icon name="document" size={28} /><strong>尚未提交补充材料</strong><span>系统自动数据正常时无需重复上传。</span></div>}
            </section>
          </div>
        </div>
      )}
    </main>
  )
}
