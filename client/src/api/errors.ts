import { isAxiosError } from 'axios'

export interface ApiErrorResult {
  general: string | null
  fields: Record<string, string>
}

interface FastApiValidationError {
  loc?: unknown
  msg?: unknown
}

function parseFieldErrors(detail: unknown): Record<string, string> {
  if (!Array.isArray(detail)) return {}
  const fields: Record<string, string> = {}
  for (const raw of detail) {
    if (typeof raw !== 'object' || raw === null) continue
    const item = raw as FastApiValidationError
    const loc = Array.isArray(item.loc) ? item.loc : []
    const fieldName =
      loc.length > 1 ? String(loc[loc.length - 1]) : loc.length === 1 ? String(loc[0]) : 'geral'
    const message = typeof item.msg === 'string' ? item.msg : 'Campo inválido'
    fields[fieldName] = message
  }
  return fields
}

export function extractApiError(error: unknown): ApiErrorResult {
  if (!isAxiosError(error)) {
    return { general: 'Erro inesperado. Tente novamente.', fields: {} }
  }
  if (error.response === undefined) {
    return {
      general: 'Não foi possível conectar ao servidor. Verifique sua conexão.',
      fields: {},
    }
  }
  const status = error.response.status
  const data = error.response.data as { detail?: unknown } | undefined
  const detail = data?.detail

  if (status === 422) {
    const fields = parseFieldErrors(detail)
    if (Object.keys(fields).length > 0) {
      return { general: null, fields }
    }
    return { general: 'Dados inválidos. Revise os campos e tente novamente.', fields: {} }
  }
  if (status === 401) {
    return {
      general: typeof detail === 'string' ? detail : 'Credenciais inválidas',
      fields: {},
    }
  }
  if (status === 409) {
    return {
      general: typeof detail === 'string' ? detail : 'Conflito ao processar a solicitação',
      fields: {},
    }
  }
  if (typeof detail === 'string') {
    return { general: detail, fields: {} }
  }
  return { general: 'Erro ao processar a solicitação. Tente novamente.', fields: {} }
}
