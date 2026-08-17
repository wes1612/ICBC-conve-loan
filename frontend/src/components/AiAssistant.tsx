import { useMemo, useState } from 'react'
import { AI_UNAVAILABLE_MESSAGE, requestAssistantMessage } from '../api'
import type {
  AssistantHistoryMessage,
  AssistantReply,
  ConnectorId,
  FullAnalysisResult,
  MaterialEvidence,
  WorkflowStep,
} from '../types'
import { Icon } from './Icon'

interface AiAssistantProps {
  currentStep: WorkflowStep
  apiOnline: boolean | null
  merchantId: string
  identityVerified: boolean
  materials: MaterialEvidence[]
  authorizedSources: ConnectorId[]
  consentConfirmed: boolean
  analysis: FullAnalysisResult | null
}

type ChatMessage = AssistantHistoryMessage & {
  id: number
  evidenceRefs?: string[]
  shouldEscalate?: boolean
}

const STEP_LABELS: Record<WorkflowStep, string> = {
  identity: '第一步 · 基本信息上传',
  verify: '第二步 · 身份核验',
  data: '第三步 · 经营材料',
  authorize: '第四步 · 数据授权',
  results: '第五步 · 授信报告',
}

const QUICK_QUESTIONS: Record<WorkflowStep, string[]> = {
  identity: ['这一步要注意什么？', '为什么需要主体资料？'],
  verify: ['为什么需要身份核验？', '核验失败怎么办？'],
  data: ['为什么需要这些材料？', '现在还缺哪些材料？'],
  authorize: ['这些授权有什么用途？', '授权时要注意什么？'],
  results: ['为什么进入这个风险等级？', '资金缺口结果怎么理解？'],
}

function AssistantContent({ content }: { content: string }) {
  const lines = content.split(/\r?\n/).map((line) => line.trim()).filter(Boolean)
  return (
    <div className="ai-message__content">
      {lines.map((line, index) => {
        const section = line.match(/^(【[^】]+】)\s*(.*)$/)
        if (section) {
          return (
            <div className="ai-message__section" key={`${index}-${line}`}>
              <strong className="ai-message__section-title">{section[1]}</strong>
              {section[2] && <p>{section[2]}</p>}
            </div>
          )
        }
        const bullet = line.match(/^[-•]\s*(.+)$/)
        if (bullet) {
          return <div className="ai-message__bullet" key={`${index}-${line}`}><span>•</span><p>{bullet[1]}</p></div>
        }
        const numbered = line.match(/^(\d+)[.、]\s*(.+)$/)
        if (numbered) {
          return <div className="ai-message__bullet" key={`${index}-${line}`}><span>{numbered[1]}.</span><p>{numbered[2]}</p></div>
        }
        return <p key={`${index}-${line}`}>{line}</p>
      })}
    </div>
  )
}

export function AiAssistant({
  currentStep,
  apiOnline,
  merchantId,
  identityVerified,
  materials,
  authorizedSources,
  consentConfirmed,
  analysis,
}: AiAssistantProps) {
  const [open, setOpen] = useState(false)
  const [draft, setDraft] = useState('')
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const context = useMemo(() => ({
    merchant_id: merchantId,
    identity_verified: identityVerified,
    materials: materials.map((item) => ({
      material_id: item.material_id,
      group: item.group,
      completeness_score: item.completeness_score,
      subject_match: item.subject_match,
      warnings: item.warnings.slice(0, 6),
    })),
    authorized_sources: authorizedSources,
    consent_confirmed: consentConfirmed,
    analysis: currentStep === 'results' ? analysis : null,
  }), [analysis, authorizedSources, consentConfirmed, currentStep, identityVerified, materials, merchantId])

  const submit = async (question: string) => {
    const message = question.trim()
    if (!message || loading) return
    const priorHistory = messages.slice(-8).map(({ role, content }) => ({ role, content }))
    const userMessage: ChatMessage = { id: Date.now(), role: 'user', content: message }
    setMessages((value) => [...value, userMessage])
    setDraft('')
    setError(null)
    setLoading(true)
    try {
      const reply: AssistantReply = await requestAssistantMessage({
        message,
        current_step: currentStep,
        context,
        history: priorHistory,
      })
      setMessages((value) => [...value, {
        id: Date.now() + 1,
        role: 'assistant',
        content: reply.answer,
        evidenceRefs: reply.evidence_refs,
        shouldEscalate: reply.should_escalate,
      }])
    } catch {
      setError(AI_UNAVAILABLE_MESSAGE)
    } finally {
      setLoading(false)
    }
  }

  return (
    <aside className={`ai-assistant ${open ? 'is-open' : ''}`} aria-label="五步授信流程助手">
      {open && (
        <div className="ai-assistant__panel">
          <header>
            <div className="ai-assistant__mark"><Icon name="spark" size={20} /></div>
            <div><strong>工小信 · 流程助手</strong><span>{STEP_LABELS[currentStep]}</span></div>
            <button type="button" onClick={() => setOpen(false)} aria-label="关闭流程助手">×</button>
          </header>

          <div className="ai-assistant__scope">
            仅解释当前流程与既有分析结果，不参与评分或授信决策。
          </div>

          <div className="ai-assistant__messages" aria-live="polite">
            {messages.length === 0 && (
              <div className="ai-assistant__empty">
                <Icon name="shield" size={24} />
                <p>可以询问本步骤的资料要求、注意事项和结果含义。</p>
              </div>
            )}
            {messages.map((message) => (
              <div className={`ai-message ai-message--${message.role}`} key={message.id}>
                {message.role === 'assistant'
                  ? <AssistantContent content={message.content} />
                  : <p>{message.content}</p>}
                {!!message.evidenceRefs?.length && (
                  <div className="ai-evidence">依据：{message.evidenceRefs.join('、')}</div>
                )}
                {message.shouldEscalate && <div className="ai-escalate">建议转人工客服确认</div>}
              </div>
            ))}
            {loading && <div className="ai-message ai-message--loading"><i /><i /><i /></div>}
            {error && <div className="ai-assistant__error"><Icon name="warning" size={17} />{error}</div>}
            {apiOnline === false && <div className="ai-assistant__error"><Icon name="warning" size={17} />后端服务离线，流程助手暂不可用。</div>}
          </div>

          <div className="ai-assistant__quick">
            {QUICK_QUESTIONS[currentStep].map((question) => (
              <button type="button" key={question} onClick={() => void submit(question)} disabled={loading || apiOnline === false}>{question}</button>
            ))}
          </div>

          <form onSubmit={(event) => { event.preventDefault(); void submit(draft) }}>
            <input
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              maxLength={500}
              placeholder="输入关于当前步骤的问题"
              disabled={loading || apiOnline === false}
            />
            <button type="submit" disabled={!draft.trim() || loading || apiOnline === false} aria-label="发送问题"><Icon name="arrow" size={18} /></button>
          </form>
        </div>
      )}
      <button className="ai-assistant__trigger" type="button" onClick={() => setOpen((value) => !value)} aria-expanded={open}>
        <Icon name="spark" size={20} />
        <span>流程助手</span>
      </button>
    </aside>
  )
}
