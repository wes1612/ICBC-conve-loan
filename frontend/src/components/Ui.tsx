import type { ReactNode } from 'react'
import type { RiskLevel } from '../types'
import { Icon, type IconName } from './Icon'

export function Button({
  children,
  variant = 'primary',
  icon,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary' | 'ghost'
  icon?: IconName
}) {
  return (
    <button className={`button button--${variant}`} {...props}>
      <span>{children}</span>
      {icon && <Icon name={icon} size={18} />}
    </button>
  )
}

export function Eyebrow({ children }: { children: ReactNode }) {
  return <div className="eyebrow">{children}</div>
}

export function RiskPill({ risk }: { risk: RiskLevel }) {
  const labels: Record<RiskLevel, string> = {
    LOW: '低风险',
    MEDIUM: '需关注',
    HIGH: '高风险',
    MANUAL_REVIEW: '人工复核',
  }
  return <span className={`risk-pill risk-pill--${risk.toLowerCase()}`}>{labels[risk]}</span>
}

export function InfoNote({
  children,
  tone = 'neutral',
}: {
  children: ReactNode
  tone?: 'neutral' | 'warning' | 'positive'
}) {
  return (
    <div className={`info-note info-note--${tone}`}>
      <Icon name={tone === 'warning' ? 'warning' : tone === 'positive' ? 'check' : 'shield'} size={18} />
      <div>{children}</div>
    </div>
  )
}

export function Metric({
  label,
  value,
  note,
}: {
  label: string
  value: ReactNode
  note?: string
}) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
      {note && <small>{note}</small>}
    </div>
  )
}
