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

// Formatador pt-BR oficial via Intl.DateTimeFormat (US-041). Mantém o shape
// "dd/mm/yyyy HH:MM" separando data e hora em dois formatters (o default da
// API adiciona vírgula entre os dois componentes em algumas versões do
// engine — evitamos construindo cada parte isoladamente).
const DATE_FORMATTER = new Intl.DateTimeFormat('pt-BR', {
  day: '2-digit',
  month: '2-digit',
  year: 'numeric',
})

const TIME_FORMATTER = new Intl.DateTimeFormat('pt-BR', {
  hour: '2-digit',
  minute: '2-digit',
  hour12: false,
})

export function formatCriadoEm(isoDate: string): string {
  const date = new Date(isoDate)
  if (Number.isNaN(date.getTime())) return isoDate
  return `${DATE_FORMATTER.format(date)} ${TIME_FORMATTER.format(date)}`
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

// ============================================================================
// Filtros por período e status (US-041) — deep-link via query string.
// ============================================================================

export const PERIODO_7D = '7d'
export const PERIODO_30D = '30d'
export const PERIODO_TODOS = 'todos'

export type PeriodoFilter = typeof PERIODO_7D | typeof PERIODO_30D | typeof PERIODO_TODOS

export const PERIODO_FILTERS: readonly { key: PeriodoFilter; label: string }[] = [
  { key: PERIODO_7D, label: 'Últimos 7 dias' },
  { key: PERIODO_30D, label: 'Últimos 30 dias' },
  { key: PERIODO_TODOS, label: 'Todos' },
]

export function parsePeriodoParam(raw: string | null): PeriodoFilter {
  if (raw === PERIODO_7D || raw === PERIODO_30D) return raw
  return PERIODO_TODOS
}

export const FILTRO_STATUS_CONCLUIDO = 'concluido'
export const FILTRO_STATUS_ERRO = 'erro'
export const FILTRO_STATUS_TODOS = 'todos'

export type StatusFilter =
  | typeof FILTRO_STATUS_CONCLUIDO
  | typeof FILTRO_STATUS_ERRO
  | typeof FILTRO_STATUS_TODOS

export const STATUS_FILTERS: readonly { key: StatusFilter; label: string }[] = [
  { key: FILTRO_STATUS_TODOS, label: 'Todos' },
  { key: FILTRO_STATUS_CONCLUIDO, label: 'Concluídas' },
  { key: FILTRO_STATUS_ERRO, label: 'Com erro' },
]

export function parseStatusFilterParam(raw: string | null): StatusFilter {
  if (raw === FILTRO_STATUS_CONCLUIDO || raw === FILTRO_STATUS_ERRO) return raw
  return FILTRO_STATUS_TODOS
}

export interface FilterableItem {
  criado_em: string
  status: string
}

function daysForPeriodo(periodo: PeriodoFilter): number | null {
  if (periodo === PERIODO_7D) return 7
  if (periodo === PERIODO_30D) return 30
  return null
}

export function matchesPeriodo<T extends FilterableItem>(
  item: T,
  periodo: PeriodoFilter,
  now: Date = new Date(),
): boolean {
  const days = daysForPeriodo(periodo)
  if (days === null) return true
  const created = new Date(item.criado_em)
  if (Number.isNaN(created.getTime())) return true
  const cutoff = now.getTime() - days * 24 * 60 * 60 * 1000
  return created.getTime() >= cutoff
}

export function matchesStatusFilter<T extends FilterableItem>(
  item: T,
  statusFilter: StatusFilter,
): boolean {
  if (statusFilter === FILTRO_STATUS_TODOS) return true
  if (statusFilter === FILTRO_STATUS_CONCLUIDO) return isConcluido(item.status)
  if (statusFilter === FILTRO_STATUS_ERRO) return isErrorStatus(item.status)
  return true
}

export function filterItems<T extends FilterableItem>(
  items: readonly T[],
  periodo: PeriodoFilter,
  statusFilter: StatusFilter,
  now: Date = new Date(),
): T[] {
  return items.filter(
    (i) => matchesPeriodo(i, periodo, now) && matchesStatusFilter(i, statusFilter),
  )
}

// ============================================================================
// Hero de evolução (US-041): sparkline + média + delta vs período anterior.
// ============================================================================

export interface SparklinePoint {
  idx: number
  nota: number
  criado_em: string
}

export interface HistoricoItemLike extends FilterableItem {
  nota_geral: number | null
}

// Sparkline ordenada do mais antigo (esq) ao mais recente (dir).
export function sparklinePoints<T extends HistoricoItemLike>(
  items: readonly T[],
): SparklinePoint[] {
  const concluidos = items.filter(
    (i) => isConcluido(i.status) && i.nota_geral !== null && !Number.isNaN(i.nota_geral),
  )
  const ordered = [...concluidos].sort(
    (a, b) => new Date(a.criado_em).getTime() - new Date(b.criado_em).getTime(),
  )
  return ordered.map((item, idx) => ({
    idx,
    nota: item.nota_geral as number,
    criado_em: item.criado_em,
  }))
}

export function averageNota<T extends HistoricoItemLike>(
  items: readonly T[],
): number | null {
  const values = items
    .filter((i) => isConcluido(i.status))
    .map((i) => i.nota_geral)
    .filter((n): n is number => n !== null && !Number.isNaN(n))
  if (values.length === 0) return null
  const sum = values.reduce((acc, v) => acc + v, 0)
  return sum / values.length
}

// Delta da média recente vs média anterior. Divide os itens ordenados
// cronologicamente em duas metades (mais antiga vs mais recente) e
// retorna `recente - antiga`. Requer pelo menos 2 concluidos, caso
// contrário retorna `null` (sem comparação possível).
export function notaTrendDelta<T extends HistoricoItemLike>(
  items: readonly T[],
): number | null {
  const points = sparklinePoints(items)
  if (points.length < 2) return null
  const mid = Math.floor(points.length / 2)
  const older = points.slice(0, mid)
  const newer = points.slice(mid)
  const avg = (arr: SparklinePoint[]) =>
    arr.reduce((acc, p) => acc + p.nota, 0) / arr.length
  if (older.length === 0 || newer.length === 0) return null
  return avg(newer) - avg(older)
}

export function formatNotaAverage(avg: number | null): string {
  if (avg === null || Number.isNaN(avg)) return '—'
  return avg.toFixed(1)
}

export function formatTrendDelta(delta: number | null): string {
  if (delta === null || Number.isNaN(delta)) return ''
  const sign = delta > 0 ? '+' : delta < 0 ? '−' : '±'
  return `${sign}${Math.abs(delta).toFixed(1)}`
}

export function trendDirection(
  delta: number | null,
): 'up' | 'down' | 'flat' | null {
  if (delta === null || Number.isNaN(delta)) return null
  const eps = 0.05
  if (delta > eps) return 'up'
  if (delta < -eps) return 'down'
  return 'flat'
}
