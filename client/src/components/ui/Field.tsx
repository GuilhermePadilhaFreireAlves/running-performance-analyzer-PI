/**
 * Field — compõe `<label>` + `<Input>` + texto de erro/hint. Quando `error`
 * é truthy, renderiza a mensagem vermelha e marca o Input como inválido;
 * `hint` aparece como auxiliar em cinza e é substituído pelo erro.
 * `aria-describedby` aponta para a mensagem ativa (erro ou hint).
 */
import { useId } from 'react'
import type { ReactNode } from 'react'
import { Input } from './Input'
import type { InputProps } from './Input'

export interface FieldProps extends Omit<InputProps, 'id' | 'invalid'> {
  label: ReactNode
  error?: string | null
  hint?: string | null
  id?: string
}

export function Field({
  label,
  error,
  hint,
  id: idFromProps,
  ...inputProps
}: FieldProps) {
  const fallbackId = useId()
  const id = idFromProps ?? fallbackId
  const hasError = Boolean(error)
  const hasHint = !hasError && Boolean(hint)
  const describedBy = hasError
    ? `${id}-error`
    : hasHint
      ? `${id}-hint`
      : undefined

  return (
    <div className="ui-field">
      <label htmlFor={id} className="ui-field-label">
        {label}
      </label>
      <Input
        id={id}
        invalid={hasError}
        aria-describedby={describedBy}
        {...inputProps}
      />
      {hasError ? (
        <p id={`${id}-error`} className="ui-field-error">
          {error}
        </p>
      ) : hasHint ? (
        <p id={`${id}-hint`} className="ui-field-hint">
          {hint}
        </p>
      ) : null}
    </div>
  )
}
