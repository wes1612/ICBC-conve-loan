import { useRef } from 'react'
import type { ApplicationDraft } from '../types'
import { Icon } from '../components/Icon'
import { Button, Eyebrow, InfoNote } from '../components/Ui'
import { isApplicationDraftValid } from '../validation'

interface IdentityPageProps {
  value: ApplicationDraft
  licenseFile: File | null
  onChange: (value: ApplicationDraft) => void
  onLicenseFileChange: (file: File | null) => void
  onBack: () => void
  onNext: () => void
}

const useOfFundsOptions = ['设备采购', '装修扩店', '旺季备货', '人员扩充', '平台活动垫资', '租金工资周转', '其他经营周转'] as const
const repaymentSourceOptions = ['经营现金流', '平台订单回款', '工行账户自动扣款', '其他经营收入'] as const
const tenorOptions = [3, 6, 9, 12, 18, 24]

export function IdentityPage({
  value,
  licenseFile,
  onChange,
  onLicenseFileChange,
  onBack,
  onNext,
}: IdentityPageProps) {
  const licenseInputRef = useRef<HTMLInputElement | null>(null)
  const update = (key: keyof ApplicationDraft, next: string | number) => onChange({ ...value, [key]: next })
  const isComplete = isApplicationDraftValid(value)
  const industries = ['美容美发', '餐饮服务', '生活服务', '宠物服务', '教育培训', '其他服务']
  const provinces = ['上海市', '北京市', '广东省', '浙江省', '江苏省', '四川省']
  const cities = value.province === '上海市'
    ? ['上海市']
    : value.province === '北京市'
      ? ['北京市']
      : ['请选择城市', '省会城市', '地级市']

  return (
    <main className="workflow page-shell">
      <div className="workflow__intro workflow__intro--simple">
        <div>
          <Eyebrow>01 · 基本信息上传</Eyebrow>
          <p>主体、收款账户与开票信息的一致性会影响经营真实性判断，请按营业执照如实填写。</p>
        </div>
      </div>

      <div className="form-layout">
        <section className="form-card">
          <div className="form-section-title"><span>01</span><div><h2>企业基本信息</h2><p>带 <b>*</b> 为后续接入的必填资料</p></div></div>
          <div className="form-grid">
            <label className="field field--wide"><span>主体名称 <b>*</b></span><input value={value.merchantName} onChange={(e) => update('merchantName', e.target.value)} placeholder="与营业执照保持一致" /></label>
            <label className="field"><span>所属行业 <b>*</b></span><input list="industry-options" value={value.industry} onChange={(e) => update('industry', e.target.value)} placeholder="请选择或填写所属行业" /><datalist id="industry-options">{industries.map((item) => <option value={item} key={item} />)}</datalist></label>
            <label className="field"><span>统一社会信用代码</span><input value={value.socialCreditCode} onChange={(e) => update('socialCreditCode', e.target.value.toUpperCase())} placeholder="18 位代码" maxLength={18} /></label>
            <label className="field"><span>经营地址 · 省</span><select value={value.province} onChange={(e) => update('province', e.target.value)}>{provinces.map((item) => <option key={item}>{item}</option>)}</select></label>
            <label className="field"><span>经营地址 · 市</span><select value={value.city} onChange={(e) => update('city', e.target.value)}>{cities.map((item) => <option key={item}>{item}</option>)}</select></label>
            <label className="field field--wide"><span>详细地址</span><input value={value.address} onChange={(e) => update('address', e.target.value)} placeholder="请填写营业执照登记地址或实际经营详细地址" /></label>
          </div>
          <div className={`upload-zone ${licenseFile ? 'is-selected' : ''}`}>
            <Icon name="upload" size={28} />
            <div><strong>营业执照</strong><span>{licenseFile?.name || '支持 PDF / JPG / PNG，单文件不超过 5MB'}</span></div>
            <input
              ref={licenseInputRef}
              className="visually-hidden-file"
              type="file"
              accept=".pdf,.jpg,.jpeg,.png"
              onChange={(event) => onLicenseFileChange(event.target.files?.[0] || null)}
            />
            <button type="button" onClick={() => licenseInputRef.current?.click()}>
              {licenseFile ? '重新选择' : '选择文件'}
            </button>
            <small>{licenseFile ? '文件已暂存，将在经营数据步骤自动提交后端校验与解析。' : '也可在经营数据步骤载入仓库内置的演示执照。'}</small>
          </div>
        </section>

        <section className="form-card">
          <div className="form-section-title"><span>02</span><div><h2>法人及贷款申请</h2><p>用于身份核验、需求匹配与申请进度通知</p></div></div>
          <div className="form-grid">
            <label className="field"><span>法人姓名 <b>*</b></span><input value={value.legalName} onChange={(e) => update('legalName', e.target.value)} placeholder="请输入法人姓名" /></label>
            <label className="field"><span>法人手机号 <b>*</b></span><input value={value.legalPhone} onChange={(e) => update('legalPhone', e.target.value)} placeholder="11 位手机号" inputMode="tel" maxLength={11} /></label>
            <label className="field field--wide"><span>法人身份证号</span><input value={value.legalIdNumber} onChange={(e) => update('legalIdNumber', e.target.value.toUpperCase())} placeholder="请输入法人身份证号" maxLength={18} /></label>
            <label className="field"><span>联系人姓名 <b>*</b></span><input value={value.contactName} onChange={(e) => update('contactName', e.target.value)} placeholder="请输入联系人姓名" /></label>
            <label className="field"><span>联系人手机号 <b>*</b></span><input value={value.contactPhone} onChange={(e) => update('contactPhone', e.target.value)} placeholder="11 位手机号" inputMode="tel" maxLength={11} /></label>
            <label className="field field--wide"><span>联系人身份证号</span><input value={value.contactIdNumber} onChange={(e) => update('contactIdNumber', e.target.value.toUpperCase())} placeholder="请输入联系人身份证号" maxLength={18} /></label>
            <label className="field"><span>本次申请金额</span><div className="money-input"><b>¥</b><input value={value.requestedAmount} onChange={(e) => update('requestedAmount', Number(e.target.value))} type="number" min="0" max="20000000" step="10000" /></div><small>仅作为需求输入，不代表承诺额度。</small></label>
            <label className="field"><span>申请期限</span><select value={value.requestedTenorMonths} onChange={(e) => update('requestedTenorMonths', Number(e.target.value))}>{tenorOptions.map((item) => <option value={item} key={item}>{item} 个月</option>)}</select><small>系统会按风险和现金流压力修正建议期限。</small></label>
            <label className="field"><span>资金用途</span><select value={value.useOfFunds} onChange={(e) => update('useOfFunds', e.target.value)}>{useOfFundsOptions.map((item) => <option value={item} key={item}>{item}</option>)}</select><small>用于匹配提款规则、补件要求和消费承接建议。</small></label>
            <label className="field"><span>主要还款来源</span><select value={value.expectedRepaymentSource} onChange={(e) => update('expectedRepaymentSource', e.target.value)}>{repaymentSourceOptions.map((item) => <option value={item} key={item}>{item}</option>)}</select><small>将与经营现金流、平台订单和授权流水交叉验证。</small></label>
          </div>
          <InfoNote tone="warning">申请金额、用途和还款来源会进入授信方案解释层；最终额度仍由评分卡、规则门控和现金流压力情景共同约束。</InfoNote>
        </section>
      </div>

      <div className="workflow__actions">
        <Button variant="ghost" onClick={onBack}>上一页</Button>
        <Button icon="arrow" onClick={onNext} disabled={!isComplete}>下一页</Button>
      </div>
    </main>
  )
}