import { useEffect, useRef, useState } from 'react'
import { describeApiError, parseMaterial } from '../api'
import { Icon, type IconName } from '../components/Icon'
import { Button, Eyebrow } from '../components/Ui'
import {
  mockMaterialEvidence,
} from '../data/materialFixtures'
import type {
  AnalysisMode,
  DemoMerchantId,
  MaterialEvidence,
  MaterialGroupId,
} from '../types'

interface DataPageProps {
  merchantId: DemoMerchantId
  demoMaterials: MaterialEvidence[]
  analysisMode: AnalysisMode
  stagedLicenseFile: File | null
  materials: MaterialEvidence[]
  onChange: (materials: MaterialEvidence[]) => void
  onBack: () => void
  onNext: () => void
}

interface MaterialConfig {
  id: MaterialGroupId
  icon: IconName
  title: string
  description: string
  required: boolean
  hint: string
  accept: string
}

const uploadGroups: MaterialConfig[] = [
  { id: 'license', icon: 'building', title: '经营主体证明', description: '营业执照或经营主体登记证明', required: true, hint: '核验主体名称、统一社会信用代码和经营状态', accept: '.pdf,.png,.jpg,.jpeg' },
  { id: 'cashflow', icon: 'database', title: '经营现金流', description: '至少连续 12 个月的流水表、PDF 或截图', required: true, hint: '用于异常识别与 P50 / P90 资金缺口预测', accept: '.xlsx,.xls,.csv,.pdf,.png,.jpg,.jpeg' },
  { id: 'statement', icon: 'document', title: '资产负债资料', description: '最近一期资产负债表或经营财务摘要', required: true, hint: '用于偿债、流动性与主体一致性核查', accept: '.xlsx,.xls,.csv,.pdf' },
  { id: 'tax', icon: 'bank', title: '纳税与开票资料', description: '近 12 个月开票及模拟申报汇总', required: true, hint: '用于经营真实性和流水交叉验证', accept: '.xlsx,.xls,.csv,.pdf' },
  { id: 'plan', icon: 'spark', title: '经营与资金计划', description: '未来三个月资本开支、订单和还本付息安排', required: true, hint: '与贷款信息、企业经营进行交叉验证。', accept: '.xlsx,.docx,.pdf' },
  { id: 'asset', icon: 'shield', title: '租赁或经营资产证明', description: '门店租赁、设备或其他经营资产材料', required: false, hint: '仅作补充证据，不作为信用贷必备抵押物', accept: '.pdf,.png,.jpg,.jpeg' },
]

const requiredGroups = uploadGroups.filter((item) => item.required).map((item) => item.id)

function fileSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  return `${(bytes / 1024).toFixed(bytes < 1024 * 100 ? 1 : 0)} KB`
}

export function DataPage({
  merchantId,
  demoMaterials,
  analysisMode,
  stagedLicenseFile,
  materials,
  onChange,
  onBack,
  onNext,
}: DataPageProps) {
  const [parsing, setParsing] = useState<MaterialGroupId | null>(null)
  const [errors, setErrors] = useState<Partial<Record<MaterialGroupId, string>>>({})
  const stagedLicenseAttempt = useRef<string | null>(null)
  const completeCount = requiredGroups.filter((group) => materials.some((item) => item.group === group)).length
  const complete = completeCount === requiredGroups.length

  const replaceMaterial = (evidence: MaterialEvidence) => {
    onChange([...materials.filter((item) => item.group !== evidence.group), evidence])
  }

  const processFile = async (group: MaterialGroupId, file: File) => {
    setParsing(group)
    setErrors((value) => ({ ...value, [group]: undefined }))
    try {
      const evidence = analysisMode === 'mock'
        ? await new Promise<MaterialEvidence>((resolve) => {
          window.setTimeout(() => resolve(mockMaterialEvidence(merchantId, group, file)), 550)
        })
        : await parseMaterial(merchantId, group, file)
      replaceMaterial(evidence)
    } catch (error) {
      setErrors((value) => ({ ...value, [group]: describeApiError(error) }))
    } finally {
      setParsing(null)
    }
  }

  useEffect(() => {
    if (!stagedLicenseFile || materials.some((item) => item.group === 'license') || parsing !== null) return
    const key = `${stagedLicenseFile.name}:${stagedLicenseFile.size}:${stagedLicenseFile.lastModified}`
    if (stagedLicenseAttempt.current === key) return
    stagedLicenseAttempt.current = key
    void processFile('license', stagedLicenseFile)
  }, [stagedLicenseFile, materials, parsing])

  const loadDemo = async (group: MaterialGroupId) => {
    setParsing(group)
    setErrors((value) => ({ ...value, [group]: undefined }))
    try {
      if (analysisMode === 'mock') {
        await new Promise((resolve) => window.setTimeout(resolve, 500))
        replaceMaterial(mockMaterialEvidence(merchantId, group))
      } else {
        const evidence = demoMaterials.find((item) => item.group === group)
        if (!evidence) throw new Error('当前随机案例缺少该组模拟记录')
        await new Promise((resolve) => window.setTimeout(resolve, 350))
        replaceMaterial(structuredClone(evidence))
      }
    } catch (error) {
      setErrors((value) => ({ ...value, [group]: describeApiError(error) }))
    } finally {
      setParsing(null)
    }
  }

  const removeMaterial = (group: MaterialGroupId) => {
    onChange(materials.filter((item) => item.group !== group))
    setErrors((value) => ({ ...value, [group]: undefined }))
  }

  return (
    <main className="workflow page-shell">
      <div className="workflow__intro workflow__intro--materials">
        <div>
          <Eyebrow>03 · 材料提交与解析</Eyebrow>
          <p>请上传公司相关文件，系统综合分析后得出可信授信结果。其中前五项为必填项，第六项为选填项。</p>
        </div>
      </div>

      <section className="upload-grid upload-grid--materials">
        {uploadGroups.map((item, index) => {
          const evidence = materials.find((material) => material.group === item.id)
          const isParsing = parsing === item.id
          return (
            <article
              className={`upload-card material-card ${evidence ? 'is-complete' : ''} ${isParsing ? 'is-parsing' : ''}`}
              key={item.id}
              onDragOver={(event) => event.preventDefault()}
              onDrop={(event) => {
                event.preventDefault()
                const file = event.dataTransfer.files[0]
                if (file && !parsing) void processFile(item.id, file)
              }}
            >
              <div className="upload-card__index">0{index + 1}</div>
              <div className="upload-card__icon"><Icon name={isParsing ? 'refresh' : evidence ? 'check' : item.icon} size={24} /></div>
              <div className="upload-card__body">
                <div className="upload-card__title"><h2>{item.title}</h2><span>{item.required ? '必交' : '可选'}</span></div>
                <p>{item.description}</p><small>{item.hint}</small>
              </div>

              {evidence ? (
                <div className="material-result">
                  <div className="material-file-row">
                    <Icon name="document" size={17} />
                    <span><strong>{evidence.file_name}</strong><small>{fileSize(evidence.size_bytes)} · {evidence.material_id} · {evidence.simulated ? '竞赛样例' : '真实读取'}</small></span>
                    <em>{evidence.completeness_score}% 完整</em>
                  </div>
                  <div className="material-metrics">
                    {evidence.extracted_metrics.map((metric) => (
                      <div className={`material-metric material-metric--${metric.tone.toLowerCase()}`} key={`${metric.label}-${metric.value}`}>
                        <span>{metric.label}</span><strong>{metric.value}</strong>
                      </div>
                    ))}
                  </div>
                  <p className="material-finding"><Icon name={evidence.subject_match ? 'check' : 'warning'} size={15} />{evidence.findings[0]}</p>
                  {evidence.warnings[0] && <p className="material-warning"><Icon name="warning" size={15} />{evidence.warnings[0]}</p>}
                  <div className="material-actions">
                    <label className="material-file-button">
                      重新选择
                      <input type="file" accept={item.accept} onChange={(event) => {
                        const file = event.currentTarget.files?.[0]
                        if (file) void processFile(item.id, file)
                        event.currentTarget.value = ''
                      }} />
                    </label>
                    <button type="button" onClick={() => removeMaterial(item.id)}>移除</button>
                  </div>
                </div>
              ) : (
                <div className="material-dropzone">
                  <Icon name={isParsing ? 'refresh' : 'upload'} size={21} />
                  <div><strong>{isParsing ? '正在校验并模拟解析…' : '拖拽文件到这里'}</strong><span>{item.accept.split(',').join(' · ')}</span></div>
                  {!isParsing && (
                    <div>
                      <label className="material-file-button">
                        选择文件
                        <input type="file" accept={item.accept} onChange={(event) => {
                          const file = event.currentTarget.files?.[0]
                          if (file) void processFile(item.id, file)
                          event.currentTarget.value = ''
                        }} />
                      </label>
                      <button type="button" className="material-demo-button" onClick={() => void loadDemo(item.id)}>载入 {merchantId} 模拟记录</button>
                    </div>
                  )}
                </div>
              )}
              {errors[item.id] && <p className="material-error"><Icon name="warning" size={15} />{errors[item.id]}</p>}
            </article>
          )
        })}
      </section>

      <div className="workflow__actions">
        <Button variant="ghost" onClick={onBack}>返回</Button>
        <Button icon="arrow" onClick={onNext} disabled={!complete || parsing !== null}>继续数据授权</Button>
      </div>
    </main>
  )
}
