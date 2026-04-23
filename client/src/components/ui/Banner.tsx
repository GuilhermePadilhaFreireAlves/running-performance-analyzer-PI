/**
 * Banner — alerta horizontal em bloco com ícone + texto. `variant` define
 * a semântica visual (success/warning/danger/info). `assertive=true` usa
 * `role="alert"` + `aria-live="assertive"` (erros que interrompem);
 * default é `role="status"` + `aria-live="polite"`.
 */
import type { ReactNode } from 'react'

export type BannerVariant = 'success' | 'warning' | 'danger' | 'info'

export interface BannerProps {
  variant?: BannerVariant
  title?: ReactNode
  children: ReactNode
  assertive?: boolean
  icon?: ReactNode
  className?: string
}

const DEFAULT_ICONS: Record<BannerVariant, string> = {
  success: '✓',
  warning: '!',
  danger: '!',
  info: 'i',
}

export function Banner({
  variant = 'info',
  title,
  children,
  assertive = false,
  icon,
  className,
}: BannerProps) {
  const classes = [
    'ui-banner',
    `ui-banner-${variant}`,
    className ?? '',
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <div
      className={classes}
      role={assertive ? 'alert' : 'status'}
      aria-live={assertive ? 'assertive' : 'polite'}
    >
      <span className="ui-banner-icon" aria-hidden="true">
        {icon ?? DEFAULT_ICONS[variant]}
      </span>
      <div className="ui-banner-body">
        {title ? <p className="ui-banner-title">{title}</p> : null}
        <p className="ui-banner-text">{children}</p>
      </div>
    </div>
  )
}
