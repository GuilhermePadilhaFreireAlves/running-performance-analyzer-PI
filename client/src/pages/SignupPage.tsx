import { useEffect, useState } from 'react'
import type { ChangeEvent, FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { extractApiError } from '../api/errors'
import { usePageTitle } from '../hooks/usePageTitle'
import { Banner, Button, Field } from '../components/ui'
import { Logo } from '../components/Logo'
import { BRAND_NAME } from '../branding'

const NIVEIS_EXPERIENCIA = [
  { value: '', label: 'Não informar' },
  { value: 'iniciante', label: 'Iniciante' },
  { value: 'intermediario', label: 'Intermediário' },
  { value: 'avancado', label: 'Avançado' },
  { value: 'profissional', label: 'Profissional' },
] as const

const NAME_FIELD_ID = 'signup-name'
const EMAIL_FIELD_ID = 'signup-email'
const SENHA_FIELD_ID = 'signup-senha'
const ALTURA_FIELD_ID = 'signup-altura'
const PESO_FIELD_ID = 'signup-peso'
const NIVEL_FIELD_ID = 'signup-nivel'

const SENHA_MIN_LENGTH = 8
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

const FIELD_ORDER = [
  { key: 'name', id: NAME_FIELD_ID },
  { key: 'email', id: EMAIL_FIELD_ID },
  { key: 'senha', id: SENHA_FIELD_ID },
  { key: 'altura_cm', id: ALTURA_FIELD_ID },
  { key: 'peso_kg', id: PESO_FIELD_ID },
  { key: 'nivel_experiencia', id: NIVEL_FIELD_ID },
] as const

function focusField(id: string): void {
  const element = document.getElementById(id)
  if (element instanceof HTMLElement) element.focus()
}

function focusFirstError(errs: Record<string, string>): void {
  for (const { key, id } of FIELD_ORDER) {
    if (errs[key]) {
      focusField(id)
      return
    }
  }
}

export default function SignupPage() {
  usePageTitle('Criar conta')
  const { signup, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const toast = useToast()

  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [mostrarSenha, setMostrarSenha] = useState(false)
  const [alturaCm, setAlturaCm] = useState('')
  const [pesoKg, setPesoKg] = useState('')
  const [nivelExperiencia, setNivelExperiencia] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [clientErrors, setClientErrors] = useState<Record<string, string>>({})
  const [apiError, setApiError] = useState<string | null>(null)
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    if (isAuthenticated) return
    if (typeof window === 'undefined') return
    const isDesktop = window.matchMedia('(min-width: 640px)').matches
    if (isDesktop) focusField(NAME_FIELD_ID)
  }, [isAuthenticated])

  if (isAuthenticated) {
    return <Navigate to="/upload" replace />
  }

  const validate = (): Record<string, string> => {
    const errs: Record<string, string> = {}
    if (!name.trim()) errs.name = 'Nome é obrigatório'
    if (!email.trim()) {
      errs.email = 'E-mail é obrigatório'
    } else if (!EMAIL_REGEX.test(email.trim())) {
      errs.email = 'Informe um e-mail válido'
    }
    if (!senha) {
      errs.senha = 'Senha é obrigatória'
    } else if (senha.length < SENHA_MIN_LENGTH) {
      errs.senha = `Senha deve ter pelo menos ${SENHA_MIN_LENGTH} caracteres`
    }
    if (!alturaCm.trim()) {
      errs.altura_cm = 'Altura é obrigatória'
    } else {
      const parsed = Number(alturaCm)
      if (!Number.isFinite(parsed) || parsed <= 0 || parsed > 300) {
        errs.altura_cm = 'Informe uma altura válida em cm (1–300)'
      }
    }
    if (pesoKg.trim()) {
      const parsed = Number(pesoKg)
      if (!Number.isFinite(parsed) || parsed <= 0 || parsed > 500) {
        errs.peso_kg = 'Informe um peso válido em kg'
      }
    }
    return errs
  }

  const errorFor = (field: string): string | undefined =>
    clientErrors[field] ?? fieldErrors[field]

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const errs = validate()
    setClientErrors(errs)
    setApiError(null)
    setFieldErrors({})
    if (Object.keys(errs).length > 0) {
      focusFirstError(errs)
      return
    }

    setSubmitting(true)
    try {
      await signup({
        name: name.trim(),
        email: email.trim(),
        senha,
        altura_cm: Number(alturaCm),
        peso_kg: pesoKg.trim() ? Number(pesoKg) : null,
        nivel_experiencia: nivelExperiencia.trim() ? nivelExperiencia.trim() : null,
      })
      toast.success('Conta criada com sucesso!')
      navigate('/upload', { replace: true })
    } catch (err) {
      const parsed = extractApiError(err)
      const nextFieldErrors = { ...parsed.fields }
      let nextGeneral = parsed.general
      if (nextGeneral && /mail/i.test(nextGeneral) && !nextFieldErrors.email) {
        nextFieldErrors.email = nextGeneral
        nextGeneral = null
      }
      setApiError(nextGeneral)
      setFieldErrors(nextFieldErrors)
      if (Object.keys(nextFieldErrors).length > 0) {
        focusFirstError(nextFieldErrors)
      }
    } finally {
      setSubmitting(false)
    }
  }

  const handleAlturaChange = (event: ChangeEvent<HTMLInputElement>) => {
    setAlturaCm(event.target.value)
  }
  const handlePesoChange = (event: ChangeEvent<HTMLInputElement>) => {
    setPesoKg(event.target.value)
  }
  const handleNivelChange = (event: ChangeEvent<HTMLSelectElement>) => {
    setNivelExperiencia(event.target.value)
  }

  return (
    <main id="main" tabIndex={-1} className="login-layout">
      <section className="login-panel">
        <div className="login-card signup-card">
          <header className="login-brand">
            <Logo size={32} title={BRAND_NAME} />
            <span className="login-brand-name">{BRAND_NAME}</span>
          </header>
          <h1 className="login-title">Criar conta</h1>
          <p className="login-subtitle">
            Em poucos minutos você recebe sua primeira análise.
          </p>
          <form
            onSubmit={handleSubmit}
            noValidate
            className="login-form signup-form"
            aria-label="Formulário de cadastro"
          >
            {apiError ? (
              <Banner variant="danger" assertive>
                {apiError}
              </Banner>
            ) : null}

            <fieldset className="signup-fieldset">
              <legend className="signup-legend">Conta</legend>
              <div className="signup-fieldset-body">
                <Field
                  id={NAME_FIELD_ID}
                  label="Nome"
                  type="text"
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  autoComplete="name"
                  error={errorFor('name') ?? null}
                />
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
                <div className="signup-password">
                  <Field
                    id={SENHA_FIELD_ID}
                    label="Senha"
                    type={mostrarSenha ? 'text' : 'password'}
                    value={senha}
                    onChange={(event) => setSenha(event.target.value)}
                    autoComplete="new-password"
                    hint={
                      errorFor('senha')
                        ? null
                        : `Mínimo ${SENHA_MIN_LENGTH} caracteres.`
                    }
                    error={errorFor('senha') ?? null}
                  />
                  <button
                    type="button"
                    className="signup-password-toggle"
                    aria-pressed={mostrarSenha}
                    aria-controls={SENHA_FIELD_ID}
                    onClick={() => setMostrarSenha((prev) => !prev)}
                  >
                    {mostrarSenha ? 'Ocultar' : 'Mostrar'} senha
                  </button>
                </div>
              </div>
            </fieldset>

            <fieldset className="signup-fieldset">
              <legend className="signup-legend">Perfil físico</legend>
              <div className="signup-fieldset-body signup-grid-2">
                <Field
                  id={ALTURA_FIELD_ID}
                  label="Altura (cm)"
                  type="number"
                  inputMode="decimal"
                  step="0.1"
                  min="1"
                  max="300"
                  value={alturaCm}
                  onChange={handleAlturaChange}
                  hint={errorFor('altura_cm') ? null : 'Ex.: 175'}
                  error={errorFor('altura_cm') ?? null}
                />
                <Field
                  id={PESO_FIELD_ID}
                  label="Peso (kg)"
                  type="number"
                  inputMode="decimal"
                  step="0.1"
                  min="1"
                  max="500"
                  value={pesoKg}
                  onChange={handlePesoChange}
                  hint={errorFor('peso_kg') ? null : 'Opcional'}
                  error={errorFor('peso_kg') ?? null}
                />
              </div>
            </fieldset>

            <fieldset className="signup-fieldset">
              <legend className="signup-legend">Experiência</legend>
              <div className="signup-fieldset-body">
                <div className="ui-field">
                  <label htmlFor={NIVEL_FIELD_ID} className="ui-field-label">
                    Nível de experiência
                  </label>
                  <select
                    id={NIVEL_FIELD_ID}
                    className="ui-input"
                    value={nivelExperiencia}
                    onChange={handleNivelChange}
                    aria-describedby={
                      errorFor('nivel_experiencia')
                        ? `${NIVEL_FIELD_ID}-error`
                        : `${NIVEL_FIELD_ID}-hint`
                    }
                  >
                    {NIVEIS_EXPERIENCIA.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                  {errorFor('nivel_experiencia') ? (
                    <p
                      id={`${NIVEL_FIELD_ID}-error`}
                      className="ui-field-error"
                    >
                      {errorFor('nivel_experiencia')}
                    </p>
                  ) : (
                    <p
                      id={`${NIVEL_FIELD_ID}-hint`}
                      className="ui-field-hint"
                    >
                      Opcional — ajuda a personalizar recomendações.
                    </p>
                  )}
                </div>
              </div>
            </fieldset>

            <Button
              type="submit"
              size="lg"
              loading={submitting}
              className="login-submit"
            >
              Criar conta
            </Button>
          </form>
          <p className="login-switch">
            Já tem conta? <Link to="/login">Entrar</Link>.
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
              <linearGradient id="signup-hero-stroke" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="rgba(255,255,255,0.95)" />
                <stop offset="100%" stopColor="rgba(255,255,255,0.45)" />
              </linearGradient>
            </defs>
            <g
              stroke="url(#signup-hero-stroke)"
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
          <p className="login-hero-tagline">
            Comece sua análise biomecânica.
          </p>
        </div>
      </aside>
    </main>
  )
}
