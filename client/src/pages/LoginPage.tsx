import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { extractApiError } from '../api/errors'
import { usePageTitle } from '../hooks/usePageTitle'

interface RedirectState {
  from?: string
}

export default function LoginPage() {
  usePageTitle('Entrar')
  const { login, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [clientErrors, setClientErrors] = useState<Record<string, string>>({})
  const [apiError, setApiError] = useState<string | null>(null)
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})

  const redirectTo = (location.state as RedirectState | null)?.from ?? '/upload'

  if (isAuthenticated) {
    return <Navigate to={redirectTo} replace />
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const errs: Record<string, string> = {}
    if (!email.trim()) errs.email = 'E-mail é obrigatório'
    if (!senha) errs.senha = 'Senha é obrigatória'

    setClientErrors(errs)
    setApiError(null)
    setFieldErrors({})
    if (Object.keys(errs).length > 0) return

    setSubmitting(true)
    try {
      await login({ email: email.trim(), senha })
      navigate(redirectTo, { replace: true })
    } catch (err) {
      const parsed = extractApiError(err)
      setApiError(parsed.general)
      setFieldErrors(parsed.fields)
    } finally {
      setSubmitting(false)
    }
  }

  const errorFor = (field: string): string | undefined =>
    clientErrors[field] ?? fieldErrors[field]

  return (
    <main className="auth-container">
      <h1>Entrar</h1>
      <form onSubmit={handleSubmit} noValidate className="auth-form" aria-label="Formulário de login">
        <label className="field">
          <span>E-mail</span>
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            autoComplete="email"
            aria-invalid={errorFor('email') ? 'true' : 'false'}
          />
          {errorFor('email') ? (
            <span className="field-error" role="alert">
              {errorFor('email')}
            </span>
          ) : null}
        </label>

        <label className="field">
          <span>Senha</span>
          <input
            type="password"
            value={senha}
            onChange={(event) => setSenha(event.target.value)}
            autoComplete="current-password"
            aria-invalid={errorFor('senha') ? 'true' : 'false'}
          />
          {errorFor('senha') ? (
            <span className="field-error" role="alert">
              {errorFor('senha')}
            </span>
          ) : null}
        </label>

        {apiError ? (
          <p className="form-error" role="alert">
            {apiError}
          </p>
        ) : null}

        <button type="submit" disabled={submitting}>
          {submitting ? 'Entrando…' : 'Entrar'}
        </button>
      </form>
      <p className="auth-switch">
        Não tem conta? <Link to="/signup">Crie a sua</Link>.
      </p>
    </main>
  )
}
