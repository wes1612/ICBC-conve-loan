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

const QUICK_QUESTIONS = [
  '消费引导策略是什么？需要我自己去申请吗？',
  '为什么我要上传支付宝、微信、美团等数据？',
  '法人和联系人的区别是什么？',
]

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
      {open && <button className="ai-assistant__dismiss-area" type="button" onClick={() => setOpen(false)} tabIndex={-1} aria-label="点击浮窗左侧区域收起小微助手" />}
      {open && (
        <div className="ai-assistant__panel" role="dialog" aria-label="小微助手对话框">
          <header className="ai-assistant__intro">
            <div>
              <strong>hi, 我是您的小微助手~</strong>
              <span>试试这样问：</span>
              <small>{STEP_LABELS[currentStep]} · 仅作解释，不参与审批</small>
            </div>
            <button className="ai-assistant__avatar assistant-smiley" type="button" onClick={() => setOpen(false)} aria-label="收起小微助手">
              <Icon name="smiley" size={36} />
            </button>
          </header>

          <div className="ai-assistant__quick">
            {QUICK_QUESTIONS.map((question) => (
              <button type="button" key={question} onClick={() => void submit(question)} disabled={loading || apiOnline === false}>{question}</button>
            ))}
          </div>

          <div className="ai-assistant__messages" aria-live="polite">
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

          <form onSubmit={(event) => { event.preventDefault(); void submit(draft) }}>
            <input
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              maxLength={500}
              placeholder="任何问题都可以在这里问小微~"
              disabled={loading || apiOnline === false}
            />
            <button className="ai-assistant__add" type="button" disabled aria-label="暂不支持添加附件" title="当前版本暂不支持附件问答">+</button>
            <button className="ai-assistant__send" type="submit" disabled={!draft.trim() || loading || apiOnline === false} aria-label="发送问题"><Icon name="arrow" size={22} /></button>
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
