import type { ApplicationDraft } from '../types'
import { Icon } from '../components/Icon'
import { Button, Eyebrow, InfoNote } from '../components/Ui'
import { validateApplicationDraft } from '../validation'

interface IdentityPageProps {
  value: ApplicationDraft
  onChange: (value: ApplicationDraft) => void
  onBack: () => void
  onNext: () => void
}

export function IdentityPage({ value, onChange, onBack, onNext }: IdentityPageProps) {
  const update = (key: keyof ApplicationDraft, next: string | number) => onChange({ ...value, [key]: next })
  const errors = validateApplicationDraft(value)
  const isComplete = Object.keys(errors).length === 0

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
            <label className="field field--wide"><span>主体名称 *</span><input aria-invalid={Boolean(errors.merchantName)} value={value.merchantName} onChange={(e) => update('merchantName', e.target.value)} placeholder="与营业执照保持一致" />{errors.merchantName && <small className="field-error">{errors.merchantName}</small>}</label>
            <label className="field"><span>所属行业 *</span><select aria-invalid={Boolean(errors.industry)} value={value.industry} onChange={(e) => update('industry', e.target.value)}><option>美容美发</option><option>餐饮服务</option><option>零售商贸</option><option>生活服务</option></select>{errors.industry && <small className="field-error">{errors.industry}</small>}</label>
            <label className="field"><span>统一社会信用代码 *</span><input aria-invalid={Boolean(errors.socialCreditCode)} value={value.socialCreditCode} onChange={(e) => update('socialCreditCode', e.target.value.toUpperCase())} placeholder="18 位代码" maxLength={18} />{errors.socialCreditCode && <small className="field-error">{errors.socialCreditCode}</small>}</label>
            <label className="field field--wide"><span>经营地址 *</span><input aria-invalid={Boolean(errors.address)} value={value.address} onChange={(e) => update('address', e.target.value)} placeholder="连锁门店请填写总店地址" />{errors.address && <small className="field-error">{errors.address}</small>}</label>
          </div>
          <InfoNote>营业执照将在“材料提交与解析”步骤统一上传，解析结果会自动核对本页主体信息。</InfoNote>
        </section>

        <section className="form-card">
          <div className="form-section-title"><span>02</span><div><h2>法人及联系人</h2><p>用于身份核验与申请进度通知</p></div></div>
          <div className="form-grid">
            <label className="field"><span>法人姓名 *</span><input aria-invalid={Boolean(errors.legalName)} value={value.legalName} onChange={(e) => update('legalName', e.target.value)} placeholder="请输入法人姓名" />{errors.legalName && <small className="field-error">{errors.legalName}</small>}</label>
            <label className="field"><span>联系人手机号 *</span><input aria-invalid={Boolean(errors.contactPhone)} value={value.contactPhone} onChange={(e) => update('contactPhone', e.target.value)} placeholder="11 位手机号" inputMode="tel" maxLength={11} />{errors.contactPhone && <small className="field-error">{errors.contactPhone}</small>}</label>
            <label className="field field--wide"><span>本次申请金额 *</span><div className="money-input"><b>¥</b><input aria-invalid={Boolean(errors.requestedAmount)} value={value.requestedAmount} onChange={(e) => update('requestedAmount', Number(e.target.value))} type="number" min="1" max="20000000" step="10000" /></div>{errors.requestedAmount ? <small className="field-error">{errors.requestedAmount}</small> : <small>仅作为需求输入，建议额度由后端模型独立计算。</small>}</label>
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
