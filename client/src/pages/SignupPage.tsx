import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { extractApiError } from '../api/errors'
import { usePageTitle } from '../hooks/usePageTitle'

const NIVEIS_EXPERIENCIA = [
  { value: '', label: 'Não informar' },
  { value: 'iniciante', label: 'Iniciante' },
  { value: 'intermediario', label: 'Intermediário' },
  { value: 'avancado', label: 'Avançado' },
  { value: 'profissional', label: 'Profissional' },
] as const

export default function SignupPage() {
  usePageTitle('Criar conta')
  const { signup, isAuthenticated } = useAuth()
  const navigate = useNavigate()

  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [alturaCm, setAlturaCm] = useState('')
  const [pesoKg, setPesoKg] = useState('')
  const [nivelExperiencia, setNivelExperiencia] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [clientErrors, setClientErrors] = useState<Record<string, string>>({})
  const [apiError, setApiError] = useState<string | null>(null)
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})

  if (isAuthenticated) {
    return <Navigate to="/upload" replace />
  }

  const validate = (): Record<string, string> => {
    const errs: Record<string, string> = {}
    if (!name.trim()) errs.name = 'Nome é obrigatório'
    if (!email.trim()) {
      errs.email = 'E-mail é obrigatório'
    } else if (!email.includes('@')) {
      errs.email = 'Informe um e-mail válido'
    }
    if (!senha) {
      errs.senha = 'Senha é obrigatória'
    } else if (senha.length < 6) {
      errs.senha = 'Senha deve ter pelo menos 6 caracteres'
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

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const errs = validate()
    setClientErrors(errs)
    setApiError(null)
    setFieldErrors({})
    if (Object.keys(errs).length > 0) return

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
      navigate('/upload', { replace: true })
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
      <h1>Criar conta</h1>
      <form
        onSubmit={handleSubmit}
        noValidate
        className="auth-form"
        aria-label="Formulário de cadastro"
      >
        <label className="field">
          <span>Nome</span>
          <input
            type="text"
            value={name}
            onChange={(event) => setName(event.target.value)}
            autoComplete="name"
            aria-invalid={errorFor('name') ? 'true' : 'false'}
          />
          {errorFor('name') ? (
            <span className="field-error" role="alert">
              {errorFor('name')}
            </span>
          ) : null}
        </label>

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
            autoComplete="new-password"
            aria-invalid={errorFor('senha') ? 'true' : 'false'}
          />
          {errorFor('senha') ? (
            <span className="field-error" role="alert">
              {errorFor('senha')}
            </span>
          ) : null}
        </label>

        <label className="field">
          <span>Altura (cm) *</span>
          <input
            type="number"
            inputMode="decimal"
            step="0.1"
            min="1"
            max="300"
            value={alturaCm}
            onChange={(event) => setAlturaCm(event.target.value)}
            aria-invalid={errorFor('altura_cm') ? 'true' : 'false'}
          />
          {errorFor('altura_cm') ? (
            <span className="field-error" role="alert">
              {errorFor('altura_cm')}
            </span>
          ) : null}
        </label>

        <label className="field">
          <span>Peso (kg)</span>
          <input
            type="number"
            inputMode="decimal"
            step="0.1"
            min="1"
            max="500"
            value={pesoKg}
            onChange={(event) => setPesoKg(event.target.value)}
            aria-invalid={errorFor('peso_kg') ? 'true' : 'false'}
          />
          {errorFor('peso_kg') ? (
            <span className="field-error" role="alert">
              {errorFor('peso_kg')}
            </span>
          ) : null}
        </label>

        <label className="field">
          <span>Nível de experiência</span>
          <select
            value={nivelExperiencia}
            onChange={(event) => setNivelExperiencia(event.target.value)}
          >
            {NIVEIS_EXPERIENCIA.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
          {errorFor('nivel_experiencia') ? (
            <span className="field-error" role="alert">
              {errorFor('nivel_experiencia')}
            </span>
          ) : null}
        </label>

        {apiError ? (
          <p className="form-error" role="alert">
            {apiError}
          </p>
        ) : null}

        <button type="submit" disabled={submitting}>
          {submitting ? 'Criando conta…' : 'Criar conta'}
        </button>
      </form>
      <p className="auth-switch">
        Já tem conta? <Link to="/login">Entrar</Link>.
      </p>
    </main>
  )
}
