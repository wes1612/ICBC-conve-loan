import { useState } from 'react'
import { Icon, type IconName } from '../components/Icon'
import { Button, Eyebrow, InfoNote } from '../components/Ui'

interface DataPageProps {
  onBack: () => void
  onNext: () => void
}

const uploadGroups: Array<{
  id: string
  icon: IconName
  title: string
  description: string
  required: boolean
  hint: string
}> = [
  { id: 'cashflow', icon: 'database', title: '经营现金流', description: '至少连续 12 个月，按月份升序', required: true, hint: '用于 P50 / P90 资金缺口预测' },
  { id: 'statement', icon: 'document', title: '资产负债资料', description: '近 12 个月或最近一期完整报表', required: true, hint: '用于偿债与流动性指标' },
  { id: 'tax', icon: 'building', title: '纳税与开票资料', description: '销售发票、采购发票及纳税申报信息', required: true, hint: '用于经营真实性交叉验证' },
  { id: 'plan', icon: 'spark', title: '经营计划', description: '未来三个月资本开支与还本付息安排', required: false, hint: '用于补充资金情景测算' },
]

export function DataPage({ onBack, onNext }: DataPageProps) {
  const [uploaded, setUploaded] = useState<string[]>(['cashflow', 'statement'])
  const toggle = (id: string) => setUploaded((items) => items.includes(id) ? items.filter((item) => item !== id) : [...items, id])
  const complete = uploadGroups.filter((item) => item.required).every((item) => uploaded.includes(item.id))

  return (
    <main className="workflow page-shell">
      <div className="workflow__intro">
        <div>
          <Eyebrow>步骤 03 · 经营资料</Eyebrow>
          <h1>补齐数据，减少误判。</h1>
          <p>资料越完整，结果越容易解释。系统不会把“未提供”误显示为零分或低风险。</p>
        </div>
        <div className="completion-ring" style={{ '--progress': `${(uploaded.length / uploadGroups.length) * 360}deg` } as React.CSSProperties}>
          <strong>{uploaded.length}<small> / {uploadGroups.length}</small></strong><span>资料组</span>
        </div>
      </div>

      <InfoNote tone="warning">
        当前后端接收结构化 JSON，尚不能自动解析上传文件。此页明确展示未来采集清单；联调时使用仓库内固定请求样例。
      </InfoNote>

      <section className="upload-grid">
        {uploadGroups.map((item, index) => {
          const isUploaded = uploaded.includes(item.id)
          return (
            <article className={`upload-card ${isUploaded ? 'is-complete' : ''}`} key={item.id}>
              <div className="upload-card__index">0{index + 1}</div>
              <div className="upload-card__icon"><Icon name={item.icon} size={24} /></div>
              <div className="upload-card__body">
                <div className="upload-card__title"><h2>{item.title}</h2><span>{item.required ? '必需' : '可选'}</span></div>
                <p>{item.description}</p><small>{item.hint}</small>
              </div>
              <button type="button" onClick={() => toggle(item.id)}>
                <Icon name={isUploaded ? 'check' : 'upload'} size={18} />
                {isUploaded ? '已使用演示数据' : '载入演示数据'}
              </button>
            </article>
          )
        })}
      </section>

      <section className="data-requirements">
        <div><Icon name="database" /><span><strong>12 个月</strong>现金流历史最低长度</span></div>
        <div><Icon name="refresh" /><span><strong>3 个月</strong>P50 / P90 预测周期</span></div>
        <div><Icon name="shield" /><span><strong>同一商户</strong>各模块 merchant_id 必须一致</span></div>
      </section>

      <div className="workflow__actions">
        <Button variant="ghost" onClick={onBack}>返回</Button>
        <Button icon="arrow" onClick={onNext} disabled={!complete}>继续数据授权</Button>
      </div>
    </main>
  )
}
