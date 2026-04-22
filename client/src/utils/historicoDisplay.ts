import {
  STATUS_CALCULANDO,
  STATUS_CONCLUIDO,
  STATUS_DETECTANDO_POSE,
  STATUS_ERRO_KEYPOINTS,
  STATUS_ERRO_MULTIPLAS,
  STATUS_PENDENTE,
  STATUS_VALIDANDO,
  errorMessageForStatus,
  isErrorStatus,
} from './videoStatus'

export const HISTORICO_PAGE_SIZE = 10

export interface StatusBadge {
  label: string
  className: string
}

const STATUS_BADGES: Record<string, StatusBadge> = {
  [STATUS_PENDENTE]: { label: 'Processando', className: 'historico-badge-progress' },
  [STATUS_VALIDANDO]: { label: 'Processando', className: 'historico-badge-progress' },
  [STATUS_DETECTANDO_POSE]: { label: 'Processando', className: 'historico-badge-progress' },
  [STATUS_CALCULANDO]: { label: 'Processando', className: 'historico-badge-progress' },
  [STATUS_CONCLUIDO]: { label: 'Concluído', className: 'historico-badge-done' },
  [STATUS_ERRO_KEYPOINTS]: { label: 'Erro', className: 'historico-badge-error' },
  [STATUS_ERRO_MULTIPLAS]: { label: 'Erro', className: 'historico-badge-error' },
}

export function statusBadge(status: string): StatusBadge {
  return (
    STATUS_BADGES[status] ?? {
      label: status,
      className: 'historico-badge-neutral',
    }
  )
}

export function isConcluido(status: string): boolean {
  return status === STATUS_CONCLUIDO
}

export function isProcessing(status: string): boolean {
  return (
    status === STATUS_PENDENTE ||
    status === STATUS_VALIDANDO ||
    status === STATUS_DETECTANDO_POSE ||
    status === STATUS_CALCULANDO
  )
}

export function errorReasonForStatus(status: string): string | null {
  return isErrorStatus(status) ? errorMessageForStatus(status) : null
}

export function formatPaceMinKm(paceMinKm: number | null): string {
  if (paceMinKm === null || Number.isNaN(paceMinKm) || paceMinKm <= 0) return '—'
  const totalSeconds = Math.round(paceMinKm * 60)
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return `${minutes}:${seconds.toString().padStart(2, '0')} /km`
}

export function formatNotaGeral(nota: number | null): string {
  if (nota === null || Number.isNaN(nota)) return '—'
  return `${nota.toFixed(1)}/10`
}

export function formatCriadoEm(isoDate: string): string {
  const date = new Date(isoDate)
  if (Number.isNaN(date.getTime())) return isoDate
  const dd = date.getDate().toString().padStart(2, '0')
  const mm = (date.getMonth() + 1).toString().padStart(2, '0')
  const yyyy = date.getFullYear().toString()
  const hh = date.getHours().toString().padStart(2, '0')
  const mi = date.getMinutes().toString().padStart(2, '0')
  return `${dd}/${mm}/${yyyy} ${hh}:${mi}`
}

export function parsePageParam(raw: string | null): number {
  if (raw === null) return 1
  const n = Number.parseInt(raw, 10)
  if (!Number.isFinite(n) || n < 1) return 1
  return n
}

export function totalPages(total: number, limit: number): number {
  if (limit <= 0) return 1
  if (total <= 0) return 1
  return Math.ceil(total / limit)
}
