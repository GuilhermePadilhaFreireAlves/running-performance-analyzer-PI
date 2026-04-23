/**
 * EmptyState — estado vazio com ilustração, título, descrição e CTA primário.
 * `illustration` deve ser um SVG decorativo (`aria-hidden`); a história em
 * sequência (US-037+) pode customizar por página. Sem CTA, não existe estado
 * vazio — garanta sempre uma próxima ação.
 */
import type { ReactNode } from 'react'

export interface EmptyStateProps {
  title: string
  description?: string
  action: ReactNode
  illustration?: ReactNode
}

export function EmptyState({
  title,
  description,
  action,
  illustration,
}: EmptyStateProps) {
  return (
    <section className="empty-state" role="status">
      <div className="empty-state-illustration" aria-hidden="true">
        {illustration ?? <DefaultIllustration />}
      </div>
      <h2 className="empty-state-title">{title}</h2>
      {description ? <p className="empty-state-description">{description}</p> : null}
      <div className="empty-state-action">{action}</div>
    </section>
  )
}

function DefaultIllustration() {
  return (
    <svg
      viewBox="0 0 120 120"
      width="120"
      height="120"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <circle cx="60" cy="60" r="52" fill="var(--brand-50)" />
      <path
        d="M38 76 L38 48 C38 44 41 41 45 41 L75 41 C79 41 82 44 82 48 L82 76"
        stroke="var(--brand-500)"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M32 76 L88 76"
        stroke="var(--brand-500)"
        strokeWidth="3"
        strokeLinecap="round"
      />
      <circle cx="52" cy="58" r="3.5" fill="var(--brand-500)" />
      <circle cx="68" cy="58" r="3.5" fill="var(--brand-500)" />
    </svg>
  )
}
