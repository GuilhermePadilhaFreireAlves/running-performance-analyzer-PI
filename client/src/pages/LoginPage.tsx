import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { extractApiError } from '../api/errors'
import { usePageTitle } from '../hooks/usePageTitle'
import { Banner, Button, Field } from '../components/ui'
import { Logo } from '../components/Logo'
import { BRAND_NAME } from '../branding'

interface RedirectState {
  from?: string
}

const EMAIL_FIELD_ID = 'login-email'
const SENHA_FIELD_ID = 'login-senha'

function focusField(id: string): void {
  const element = document.getElementById(id)
  if (element instanceof HTMLElement) element.focus()
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

  useEffect(() => {
    if (isAuthenticated) return
    if (typeof window === 'undefined') return
    const isDesktop = window.matchMedia('(min-width: 640px)').matches
    if (isDesktop) focusField(EMAIL_FIELD_ID)
  }, [isAuthenticated])

  if (isAuthenticated) {
    return <Navigate to={redirectTo} replace />
  }

  const errorFor = (field: string): string | undefined =>
    clientErrors[field] ?? fieldErrors[field]

  const focusFirstError = (errs: Record<string, string>) => {
    if (errs.email) focusField(EMAIL_FIELD_ID)
    else if (errs.senha) focusField(SENHA_FIELD_ID)
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const errs: Record<string, string> = {}
    if (!email.trim()) errs.email = 'E-mail é obrigatório'
    if (!senha) errs.senha = 'Senha é obrigatória'

    setClientErrors(errs)
    setApiError(null)
    setFieldErrors({})
    if (Object.keys(errs).length > 0) {
      focusFirstError(errs)
      return
    }

    setSubmitting(true)
    try {
      await login({ email: email.trim(), senha })
      navigate(redirectTo, { replace: true })
    } catch (err) {
      const parsed = extractApiError(err)
      setApiError(parsed.general)
      setFieldErrors(parsed.fields)
      if (Object.keys(parsed.fields).length > 0) {
        focusFirstError(parsed.fields)
      } else {
        focusField(EMAIL_FIELD_ID)
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main id="main" tabIndex={-1} className="login-layout">
      <section className="login-panel">
        <div className="login-card">
          <header className="login-brand">
            <Logo size={32} title={BRAND_NAME} />
            <span className="login-brand-name">{BRAND_NAME}</span>
          </header>
          <h1 className="login-title">Entrar</h1>
          <p className="login-subtitle">Acesse sua conta para ver suas análises.</p>
          <form
            onSubmit={handleSubmit}
            noValidate
            className="login-form"
            aria-label="Formulário de login"
          >
            {apiError ? (
              <Banner variant="danger" assertive>
                {apiError}
              </Banner>
            ) : null}

            <Field
              id={EMAIL_FIELD_ID}
              label="E-mail"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              autoComplete="email"
              inputMode="email"
              spellCheck={false}
              error={errorFor('email') ?? null}
            />

            <Field
              id={SENHA_FIELD_ID}
              label="Senha"
              type="password"
              value={senha}
              onChange={(event) => setSenha(event.target.value)}
              autoComplete="current-password"
              error={errorFor('senha') ?? null}
            />

            <Button type="submit" size="lg" loading={submitting} className="login-submit">
              Entrar
            </Button>
          </form>
          <p className="login-switch">
            Não tem conta? <Link to="/signup">Criar conta</Link>.
          </p>
        </div>
      </section>
      <aside className="login-hero" aria-hidden="true">
        <div className="login-hero-inner">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 400 400"
            className="login-hero-art"
            focusable="false"
          >
            <defs>
              <linearGradient id="login-hero-stroke" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="rgba(255,255,255,0.95)" />
                <stop offset="100%" stopColor="rgba(255,255,255,0.45)" />
              </linearGradient>
            </defs>
            <g
              stroke="url(#login-hero-stroke)"
              strokeWidth="14"
              strokeLinecap="round"
              fill="none"
            >
              <path d="M60 300 L140 140" />
              <path d="M140 320 L220 160" opacity="0.75" />
              <path d="M220 340 L300 180" opacity="0.55" />
              <path d="M300 360 L360 240" opacity="0.35" />
            </g>
            <g stroke="rgba(255,255,255,0.4)" strokeWidth="3" strokeLinecap="round">
              <path d="M48 360 L360 360" />
            </g>
          </svg>
          <p className="login-hero-tagline">Análise biomecânica de corrida.</p>
        </div>
      </aside>
    </main>
  )
}
