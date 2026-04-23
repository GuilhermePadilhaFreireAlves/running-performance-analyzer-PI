/**
 * ErrorState — estado de erro com ícone, título, mensagem e ações de
 * recuperação. "No dead ends": toda tela que exibe erro oferece pelo menos
 * uma próxima ação — `onRetry` (Tentar novamente) e/ou `backTo`
 * (link de fallback). Se nenhuma for fornecida, o componente exige via
 * prop `action` um CTA custom.
 */
import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { Button } from '../Button'

export interface ErrorStateProps {
  title?: string
  message: string
  onRetry?: () => void
  retryLoading?: boolean
  backTo?: { to: string; label: string }
  action?: ReactNode
}

export function ErrorState({
  title = 'Algo deu errado',
  message,
  onRetry,
  retryLoading = false,
  backTo,
  action,
}: ErrorStateProps) {
  return (
    <section className="error-state" role="alert" aria-live="assertive">
      <div className="error-state-icon" aria-hidden="true">
        <AlertIcon />
      </div>
      <h2 className="error-state-title">{title}</h2>
      <p className="error-state-message">{message}</p>
      <div className="error-state-actions">
        {onRetry ? (
          <Button variant="primary" onClick={onRetry} loading={retryLoading}>
            Tentar novamente
          </Button>
        ) : null}
        {backTo ? (
          <Link to={backTo.to} className="error-state-back-link">
            {backTo.label}
          </Link>
        ) : null}
        {action}
      </div>
    </section>
  )
}

function AlertIcon() {
  return (
    <svg
      viewBox="0 0 48 48"
      width="48"
      height="48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <circle cx="24" cy="24" r="22" fill="var(--danger-soft)" />
      <path
        d="M24 14 L24 28"
        stroke="var(--danger)"
        strokeWidth="3"
        strokeLinecap="round"
      />
      <circle cx="24" cy="34" r="2" fill="var(--danger)" />
    </svg>
  )
}
