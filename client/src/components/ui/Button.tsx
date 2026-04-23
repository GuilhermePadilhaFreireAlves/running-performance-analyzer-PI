/**
 * Button — botão com variantes primary/secondary/ghost/danger em tamanhos
 * sm/md/lg. `loading=true` exibe um spinner inline sem apagar o label e
 * marca o botão como `aria-busy` + `disabled` para prevenir double-click.
 */
import type { ButtonHTMLAttributes, ReactNode } from 'react'

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger'
export type ButtonSize = 'sm' | 'md' | 'lg'

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
  loading?: boolean
  children: ReactNode
}

export function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled,
  className,
  children,
  type,
  ...rest
}: ButtonProps) {
  const classes = [
    'ui-button',
    `ui-button-${variant}`,
    `ui-button-${size}`,
    loading ? 'ui-button-loading' : '',
    className ?? '',
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <button
      type={type ?? 'button'}
      className={classes}
      disabled={disabled || loading}
      aria-busy={loading ? 'true' : undefined}
      {...rest}
    >
      {loading ? (
        <svg
          className="ui-button-spinner"
          viewBox="0 0 16 16"
          aria-hidden="true"
          focusable="false"
        >
          <circle
            className="ui-button-spinner-track"
            cx="8"
            cy="8"
            r="6"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          />
          <path
            className="ui-button-spinner-arc"
            d="M14 8a6 6 0 0 0-6-6"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
          />
        </svg>
      ) : null}
      <span className="ui-button-label">{children}</span>
    </button>
  )
}
