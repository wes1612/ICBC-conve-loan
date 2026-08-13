import type { ApplicationDraft } from './types'

export type ApplicationField = keyof ApplicationDraft
export type ApplicationErrors = Partial<Record<ApplicationField, string>>

const CREDIT_CODE = /^[0-9A-Z]{18}$/
const MOBILE_PHONE = /^1[3-9]\d{9}$/
const ID_NUMBER = /^\d{17}[0-9X]$/

export function validateApplicationDraft(value: ApplicationDraft): ApplicationErrors {
  const errors: ApplicationErrors = {}

  if (value.merchantName.trim().length < 2) errors.merchantName = '请输入完整主体名称'
  if (!value.industry.trim()) errors.industry = '请选择所属行业'
  if (!CREDIT_CODE.test(value.socialCreditCode.trim().toUpperCase())) {
    errors.socialCreditCode = '请输入 18 位统一社会信用代码'
  }
  if (!value.province.trim()) errors.province = '请选择经营地址所在省份'
  if (!value.city.trim() || value.city === '请选择城市') errors.city = '请选择经营地址所在城市'
  if (value.address.trim().length < 5) errors.address = '请输入完整经营地址'
  if (value.legalName.trim().length < 2) errors.legalName = '请输入完整法人姓名'
  if (!MOBILE_PHONE.test(value.legalPhone.trim())) errors.legalPhone = '请输入有效的法人手机号'
  if (value.legalIdNumber.trim() && !ID_NUMBER.test(value.legalIdNumber.trim().toUpperCase())) {
    errors.legalIdNumber = '请输入有效的 18 位法人身份证号'
  }
  if (value.contactName.trim().length < 2) errors.contactName = '请输入完整联系人姓名'
  if (!MOBILE_PHONE.test(value.contactPhone.trim())) errors.contactPhone = '请输入有效的 11 位手机号'
  if (value.contactIdNumber.trim() && !ID_NUMBER.test(value.contactIdNumber.trim().toUpperCase())) {
    errors.contactIdNumber = '请输入有效的 18 位联系人身份证号'
  }
  if (!Number.isFinite(value.requestedAmount) || value.requestedAmount <= 0) {
    errors.requestedAmount = '申请金额必须大于 0'
  } else if (value.requestedAmount > 20_000_000) {
    errors.requestedAmount = 'MVP 单笔申请金额不能超过 2000 万元'
  }

  return errors
}

export function isApplicationDraftValid(value: ApplicationDraft): boolean {
  return Object.keys(validateApplicationDraft(value)).length === 0
}
