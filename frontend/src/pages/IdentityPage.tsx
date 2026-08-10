import type { ApplicationDraft } from '../types'
import { Icon } from '../components/Icon'
import { Button, Eyebrow, InfoNote } from '../components/Ui'

interface IdentityPageProps {
  value: ApplicationDraft
  onChange: (value: ApplicationDraft) => void
  onBack: () => void
  onNext: () => void
}

export function IdentityPage({ value, onChange, onBack, onNext }: IdentityPageProps) {
  const update = (key: keyof ApplicationDraft, next: string | number) => onChange({ ...value, [key]: next })
  const isComplete = value.merchantName && value.industry && value.legalName && value.contactPhone

  return (
    <main className="workflow page-shell">
      <div className="workflow__intro">
        <div>
          <Eyebrow>步骤 01 · 主体资料</Eyebrow>
          <h1>先确认，是谁在经营。</h1>
          <p>主体、收款账户与开票信息的一致性会影响经营真实性判断，请按营业执照如实填写。</p>
        </div>
        <div className="security-mark"><Icon name="lock" /><span>资料仅用于本次授信测算</span></div>
      </div>

      <div className="form-layout">
        <section className="form-card">
          <div className="form-section-title"><span>01</span><div><h2>企业基本信息</h2><p>带 * 为后续接入的必填资料</p></div></div>
          <div className="form-grid">
            <label className="field field--wide"><span>主体名称 *</span><input value={value.merchantName} onChange={(e) => update('merchantName', e.target.value)} placeholder="与营业执照保持一致" /></label>
            <label className="field"><span>所属行业 *</span><select value={value.industry} onChange={(e) => update('industry', e.target.value)}><option>美容美发</option><option>餐饮服务</option><option>零售商贸</option><option>生活服务</option></select></label>
            <label className="field"><span>统一社会信用代码</span><input value={value.socialCreditCode} onChange={(e) => update('socialCreditCode', e.target.value)} placeholder="18 位代码" /></label>
            <label className="field field--wide"><span>经营地址</span><input value={value.address} onChange={(e) => update('address', e.target.value)} placeholder="连锁门店请填写总店地址" /></label>
          </div>
          <div className="upload-zone">
            <Icon name="upload" size={28} />
            <div><strong>营业执照</strong><span>支持 PDF / JPG / PNG，单文件不超过 10MB</span></div>
            <button type="button">选择文件</button>
            <small>文件解析服务尚待后端接入；当前页面保存填写状态。</small>
          </div>
        </section>

        <section className="form-card">
          <div className="form-section-title"><span>02</span><div><h2>法人及联系人</h2><p>用于身份核验与申请进度通知</p></div></div>
          <div className="form-grid">
            <label className="field"><span>法人姓名 *</span><input value={value.legalName} onChange={(e) => update('legalName', e.target.value)} placeholder="请输入法人姓名" /></label>
            <label className="field"><span>联系人手机号 *</span><input value={value.contactPhone} onChange={(e) => update('contactPhone', e.target.value)} placeholder="11 位手机号" inputMode="tel" /></label>
            <label className="field field--wide"><span>本次申请金额</span><div className="money-input"><b>¥</b><input value={value.requestedAmount} onChange={(e) => update('requestedAmount', Number(e.target.value))} type="number" min="0" step="10000" /></div><small>仅作为需求输入，建议额度由后端模型独立计算。</small></label>
          </div>
          <InfoNote tone="warning">请勿将“申请金额”理解为承诺额度。系统会结合分数、稳定性与承接能力返回建议额度。</InfoNote>
        </section>
      </div>

      <div className="workflow__actions">
        <Button variant="ghost" onClick={onBack}>返回</Button>
        <Button icon="arrow" onClick={onNext} disabled={!isComplete}>继续法人核验</Button>
      </div>
    </main>
  )
}
