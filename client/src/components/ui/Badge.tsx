/**
 * Badge — chip semântico pequeno (success/warning/danger/info/neutral).
 * Use em listas/tabelas para rotular status ou severidade.
 */
import type { ReactNode } from 'react'

export type BadgeVariant = 'success' | 'warning' | 'danger' | 'info' | 'neutral'

export interface BadgeProps {
  variant?: BadgeVariant
  className?: string
  children: ReactNode
}

export function Badge({
  variant = 'neutral',
  className,
  children,
}: BadgeProps) {
  const classes = [
    'ui-badge',
    `ui-badge-${variant}`,
    className ?? '',
  ]
    .filter(Boolean)
    .join(' ')

  return <span className={classes}>{children}</span>
}
