/**
 * Input — `<input>` com `font-size: 16px` no mobile (evita o zoom automático
 * do iOS ao focar) e estilo consistente de foco/invalid. Propaga todos os
 * atributos nativos; `invalid` define `aria-invalid` e borda vermelha.
 */
import type { InputHTMLAttributes } from 'react'

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  invalid?: boolean
}

export function Input({ invalid, className, ...rest }: InputProps) {
  const classes = [
    'ui-input',
    invalid ? 'ui-input-invalid' : '',
    className ?? '',
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <input
      className={classes}
      aria-invalid={invalid ? 'true' : undefined}
      {...rest}
    />
  )
}
