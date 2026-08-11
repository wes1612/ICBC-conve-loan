import type {
  DemoCase,
  ExtractedMetric,
  MaterialEvidence,
  MaterialGroupId,
} from '../types'

interface Preset {
  completeness: number
  period?: number
  subjectMatch: boolean
  metrics: ExtractedMetric[]
  findings: string[]
  warnings?: string[]
}

export const materialGroups: MaterialGroupId[] = [
  'license', 'cashflow', 'statement', 'tax', 'plan', 'asset',
]

export const sampleFileNames: Record<MaterialGroupId, string> = {
  license: 'business_license.pdf',
  cashflow: 'cashflow_12m.xlsx',
  statement: 'financial_statement.pdf',
  tax: 'tax_invoice_12m.xlsx',
  plan: 'business_plan.pdf',
  asset: 'lease_asset_proof.pdf',
}

const presets: Record<DemoCase, Record<MaterialGroupId, Preset>> = {
  normal: {
    license: { completeness: 100, subjectMatch: true, metrics: [{ label: '主体状态', value: '存续', tone: 'POSITIVE' }, { label: '证照有效期', value: '长期', tone: 'POSITIVE' }], findings: ['统一社会信用代码与申请信息一致', '经营主体与法人核验结果一致'] },
    cashflow: { completeness: 98, period: 12, subjectMatch: true, metrics: [{ label: '月均经营流入', value: '¥95,667', tone: 'POSITIVE' }, { label: '流水完整度', value: '98%', tone: 'POSITIVE' }, { label: '明显异常', value: '0 笔', tone: 'POSITIVE' }], findings: ['识别到连续 12 个月经营流水', '收款趋势稳定且主体一致'] },
    statement: { completeness: 96, subjectMatch: true, metrics: [{ label: '资产负债率', value: '34.2%', tone: 'POSITIVE' }, { label: '流动比率', value: '1.86', tone: 'POSITIVE' }], findings: ['最近一期资产负债资料字段完整', '短期偿债覆盖处于样例安全区间'] },
    tax: { completeness: 97, period: 12, subjectMatch: true, metrics: [{ label: '开票覆盖率', value: '95.1%', tone: 'POSITIVE' }, { label: '连续申报', value: '12 个月', tone: 'POSITIVE' }], findings: ['开票收入与经营流水基本匹配', '样例期间未发现断档申报'] },
    plan: { completeness: 95, period: 3, subjectMatch: true, metrics: [{ label: '计划资本开支', value: '¥20,000', tone: 'NEUTRAL' }, { label: '未来偿债支出', value: '¥8,000', tone: 'NEUTRAL' }], findings: ['未来三个月资金用途清晰', '计划支出已纳入资金缺口压力测试'] },
    asset: { completeness: 92, subjectMatch: true, metrics: [{ label: '剩余租期', value: '18 个月', tone: 'POSITIVE' }, { label: '设备账面价值', value: '¥160,000', tone: 'NEUTRAL' }], findings: ['门店租赁关系与经营地址一致', '该材料仅作补充证据，不作为授信必备抵押物'] },
  },
  review: {
    license: { completeness: 94, subjectMatch: true, metrics: [{ label: '主体状态', value: '存续', tone: 'POSITIVE' }, { label: '经营状态', value: '存在关注项', tone: 'WARNING' }], findings: ['统一社会信用代码与申请信息一致', '工商经营状态需结合其他材料复核'], warnings: ['许可信息中存在待核实经营状态备注'] },
    cashflow: { completeness: 82, period: 12, subjectMatch: false, metrics: [{ label: '月均经营流入', value: '¥87,417', tone: 'NEUTRAL' }, { label: '疑似异常交易', value: '17 笔', tone: 'DANGER' }, { label: '个人账户占比', value: '31%', tone: 'WARNING' }], findings: ['识别到连续 12 个月流水', '发现整数金额重复、夜间交易集中和快速进出'], warnings: ['部分交易对手及收款账户与申请主体不一致'] },
    statement: { completeness: 78, subjectMatch: false, metrics: [{ label: '资产负债率', value: '68.4%', tone: 'WARNING' }, { label: '流动比率', value: '0.91', tone: 'DANGER' }], findings: ['短期负债对流动资产形成压力', '部分账户主体需补充说明'], warnings: ['报表主体与部分流水账户名称不一致'] },
    tax: { completeness: 74, period: 10, subjectMatch: true, metrics: [{ label: '开票覆盖率', value: '62.3%', tone: 'WARNING' }, { label: '连续申报', value: '10 / 12 个月', tone: 'WARNING' }], findings: ['开票收入低于经营流水', '存在两个月申报资料缺口'], warnings: ['建议补充缺失月份申报记录及未开票收入说明'] },
    plan: { completeness: 80, period: 3, subjectMatch: true, metrics: [{ label: '计划资本开支', value: '¥150,000', tone: 'WARNING' }, { label: '未来偿债支出', value: '¥45,000', tone: 'WARNING' }], findings: ['扩店投入与偿债支出同期发生', '计划支出将放大 P90 资金缺口'], warnings: ['建议补充订单回款安排和备用资金来源'] },
    asset: { completeness: 68, subjectMatch: true, metrics: [{ label: '剩余租期', value: '4 个月', tone: 'WARNING' }, { label: '设备证明', value: '部分缺失', tone: 'WARNING' }], findings: ['经营场所剩余租期较短', '该材料仅作补充证据，不作为授信必备抵押物'], warnings: ['建议补充续租意向或新经营场所安排'] },
  },
}

export function mockMaterialEvidence(
  demoCase: DemoCase,
  group: MaterialGroupId,
  file?: Pick<File, 'name' | 'size' | 'type'>,
): MaterialEvidence {
  const merchantId = demoCase === 'normal' ? 'M001' : 'M005'
  const preset = presets[demoCase][group]
  const ordinal = materialGroups.indexOf(group) + 1
  const fileName = file?.name || `${merchantId}_${sampleFileNames[group]}`
  return {
    material_id: `MAT-${merchantId}-${group.toUpperCase()}-MOCK${ordinal}`,
    merchant_id: merchantId,
    group,
    file_name: fileName,
    media_type: file?.type || (fileName.endsWith('.xlsx') ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' : 'application/pdf'),
    size_bytes: file?.size || 4096 + ordinal * 128,
    sha256: ordinal.toString(16).padStart(64, '0'),
    parse_status: 'PARSED',
    simulated: true,
    completeness_score: preset.completeness,
    period_months: preset.period ?? null,
    subject_match: preset.subjectMatch,
    extracted_metrics: preset.metrics,
    findings: preset.findings,
    warnings: preset.warnings || [],
  }
}

