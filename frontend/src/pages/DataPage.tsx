import { useEffect, useRef, useState } from 'react'
import { describeApiError, downloadDemoMaterial, parseMaterial } from '../api'
import { Icon, type IconName } from '../components/Icon'
import { Button, Eyebrow, InfoNote } from '../components/Ui'
import {
  mockMaterialEvidence,
  sampleFileNames,
} from '../data/materialFixtures'
import type {
  AnalysisMode,
  DemoCase,
  MaterialEvidence,
  MaterialGroupId,
} from '../types'

interface DataPageProps {
  merchantId: string
  demoCase: DemoCase
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
  { id: 'plan', icon: 'spark', title: '经营与资金计划', description: '未来三个月资本开支、订单和还本付息安排', required: true, hint: '避免把未知未来支出错误解释为零', accept: '.xlsx,.docx,.pdf' },
  { id: 'asset', icon: 'shield', title: '租赁或经营资产证明', description: '门店租赁、设备或其他经营资产材料', required: false, hint: '仅作补充证据，不作为信用贷必备抵押物', accept: '.pdf,.png,.jpg,.jpeg' },
]

const requiredGroups = uploadGroups.filter((item) => item.required).map((item) => item.id)

function fileSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  return `${(bytes / 1024).toFixed(bytes < 1024 * 100 ? 1 : 0)} KB`
}

export function DataPage({
  merchantId,
  demoCase,
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
          window.setTimeout(() => resolve(mockMaterialEvidence(demoCase, group, file)), 550)
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
        replaceMaterial(mockMaterialEvidence(demoCase, group))
      } else {
        const file = await downloadDemoMaterial(merchantId, group, sampleFileNames[group])
        const evidence = await parseMaterial(merchantId, group, file)
        replaceMaterial(evidence)
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
      <div className="workflow__intro">
        <div>
          <Eyebrow>步骤 03 · 材料提交与解析</Eyebrow>
          <h1>让每个结论，都能回到一份材料。</h1>
          <p>上传真实文件或载入仓库内置样例。系统先校验文件，再生成可追溯的结构化摘要。</p>
        </div>
        <div className="completion-ring" style={{ '--progress': `${(completeCount / requiredGroups.length) * 360}deg` } as React.CSSProperties}>
          <strong>{completeCount}<small> / {requiredGroups.length}</small></strong><span>必交材料</span>
        </div>
      </div>

      <InfoNote tone="warning">
        当前为<strong>竞赛模拟解析</strong>：文件会真实发送到后端完成格式、大小、签名和摘要校验；OCR 与指标提取使用 M001/M005 固定规则，不冒充真实银行或税务接口。
      </InfoNote>

      <section className="material-toolbar" aria-label="材料提交说明">
        <div><Icon name="upload" /><span><strong>真实文件交互</strong>支持选择或拖拽，单个文件不超过 5 MB</span></div>
        <div><Icon name="spark" /><span><strong>一键演示</strong>自动下载仓库中的对应 PDF / Excel 再提交解析</span></div>
        <div><Icon name="shield" /><span><strong>证据可追溯</strong>材料编号和摘要会随综合分析进入后端审核证据</span></div>
      </section>

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
                    <span><strong>{evidence.file_name}</strong><small>{fileSize(evidence.size_bytes)} · {evidence.material_id}</small></span>
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
                      <button type="button" className="material-demo-button" onClick={() => void loadDemo(item.id)}>载入 {merchantId} 样例</button>
                    </div>
                  )}
                </div>
              )}
              {errors[item.id] && <p className="material-error"><Icon name="warning" size={15} />{errors[item.id]}</p>}
            </article>
          )
        })}
      </section>

      <section className="data-requirements">
        <div><Icon name="database" /><span><strong>12 个月</strong>流水与纳税历史推荐长度</span></div>
        <div><Icon name="refresh" /><span><strong>3 个月</strong>P50 / P90 预测周期</span></div>
        <div><Icon name="shield" /><span><strong>5 MB</strong>单份材料上传上限</span></div>
      </section>

      <div className="workflow__actions">
        <Button variant="ghost" onClick={onBack}>返回</Button>
        <Button icon="arrow" onClick={onNext} disabled={!complete || parsing !== null}>继续数据授权</Button>
      </div>
    </main>
  )
}
