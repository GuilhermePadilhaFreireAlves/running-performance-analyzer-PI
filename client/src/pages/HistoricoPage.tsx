import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import {
  getHistoricoRequest,
  type HistoricoItem,
  type HistoricoResponse,
} from '../api/historico'
import { extractApiError } from '../api/errors'
import {
  averageNota,
  errorReasonForStatus,
  filterItems,
  FILTRO_STATUS_TODOS,
  formatCriadoEm,
  formatNotaAverage,
  formatNotaGeral,
  formatPaceMinKm,
  formatTrendDelta,
  HISTORICO_PAGE_SIZE,
  isConcluido,
  notaTrendDelta,
  parsePageParam,
  parsePeriodoParam,
  parseStatusFilterParam,
  PERIODO_FILTERS,
  PERIODO_TODOS,
  sparklinePoints,
  STATUS_FILTERS,
  statusBadge,
  totalPages,
  trendDirection,
  type PeriodoFilter,
  type StatusFilter,
} from '../utils/historicoDisplay'
import { usePageTitle } from '../hooks/usePageTitle'
import { useToast } from '../context/ToastContext'
import {
  Badge,
  Button,
  Card,
  EmptyState,
  ErrorState,
  LoadingState,
} from '../components/ui'
import { Sparkline } from '../components/historico/Sparkline'

const SCROLL_STORAGE_KEY = 'historico:scroll'

export default function HistoricoPage() {
  usePageTitle('Histórico')
  const [searchParams, setSearchParams] = useSearchParams()
  const navigate = useNavigate()
  const toast = useToast()
  const page = parsePageParam(searchParams.get('page'))
  const periodo = parsePeriodoParam(searchParams.get('periodo'))
  const statusFilter = parseStatusFilterParam(searchParams.get('status'))
  const [data, setData] = useState<HistoricoResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedErrorId, setSelectedErrorId] = useState<number | null>(null)
  const [retryCount, setRetryCount] = useState(0)
  const restoredScrollRef = useRef(false)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    setSelectedErrorId(null)
    getHistoricoRequest({ page, limit: HISTORICO_PAGE_SIZE })
      .then((resp) => {
        if (cancelled) return
        setData(resp)
      })
      .catch((err: unknown) => {
        if (cancelled) return
        const { general } = extractApiError(err)
        const message = general ?? 'Não foi possível carregar o histórico.'
        setError(message)
        toast.error(message)
      })
      .finally(() => {
        if (cancelled) return
        setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [page, retryCount, toast])

  // Restaura scroll após o primeiro carregamento bem-sucedido (back/forward).
  useEffect(() => {
    if (loading || error || data === null) return
    if (restoredScrollRef.current) return
    restoredScrollRef.current = true
    try {
      const saved = sessionStorage.getItem(SCROLL_STORAGE_KEY)
      if (saved !== null) {
        const y = Number.parseInt(saved, 10)
        if (Number.isFinite(y) && y > 0) {
          window.scrollTo({ top: y, behavior: 'auto' })
        }
        sessionStorage.removeItem(SCROLL_STORAGE_KEY)
      }
    } catch {
      // sessionStorage indisponível — segue sem restaurar.
    }
  }, [loading, error, data])

  const handleRetry = useCallback(() => setRetryCount((c) => c + 1), [])

  const updateParams = (mutator: (next: URLSearchParams) => void) => {
    const next = new URLSearchParams(searchParams)
    mutator(next)
    setSearchParams(next)
  }

  const goToPage = (target: number) => {
    updateParams((next) => next.set('page', target.toString()))
  }

  const setPeriodo = (next: PeriodoFilter) => {
    updateParams((nextParams) => {
      if (next === PERIODO_TODOS) {
        nextParams.delete('periodo')
      } else {
        nextParams.set('periodo', next)
      }
      // Reset to page 1 when changing filters: the current page index loses
      // meaning since the visible set just changed.
      nextParams.delete('page')
    })
  }

  const setStatusFilter = (next: StatusFilter) => {
    updateParams((nextParams) => {
      if (next === FILTRO_STATUS_TODOS) {
        nextParams.delete('status')
      } else {
        nextParams.set('status', next)
      }
      nextParams.delete('page')
    })
  }

  const persistScrollAndNavigate = (path: string) => {
    try {
      sessionStorage.setItem(SCROLL_STORAGE_KEY, window.scrollY.toString())
    } catch {
      // ignore
    }
    navigate(path)
  }

  const handleItemClick = (item: HistoricoItem) => {
    if (isConcluido(item.status)) {
      persistScrollAndNavigate(`/analysis/${item.id}`)
      return
    }
    if (errorReasonForStatus(item.status)) {
      setSelectedErrorId((current) => (current === item.id ? null : item.id))
    }
  }

  const allItems = data?.items ?? []
  const visibleItems = useMemo(
    () => filterItems(allItems, periodo, statusFilter),
    [allItems, periodo, statusFilter],
  )

  // O hero usa SEMPRE os itens da página corrente (sem filtros) — é o
  // resumo de evolução, não da fatia filtrada — para que o stat de
  // tendência se mantenha estável quando o usuário troca os filtros.
  const sparkPoints = useMemo(() => sparklinePoints(allItems), [allItems])
  const avg = useMemo(() => averageNota(allItems), [allItems])
  const trendDelta = useMemo(() => notaTrendDelta(allItems), [allItems])

  const pages = data ? totalPages(data.total, data.limit) : 1
  const hasPrev = page > 1
  const hasNext = data !== null && page < pages

  const filtersActive = periodo !== PERIODO_TODOS || statusFilter !== FILTRO_STATUS_TODOS
  const filteredOutAll =
    !loading &&
    !error &&
    data !== null &&
    allItems.length > 0 &&
    visibleItems.length === 0

  return (
    <main id="main" tabIndex={-1} className="historico-container">
      <header className="historico-header">
        <h1>Histórico de análises</h1>
      </header>

      {loading && <LoadingState variant="historico" label="Carregando histórico" />}

      {error && !loading && (
        <ErrorState
          message={error}
          onRetry={handleRetry}
          backTo={{ to: '/upload', label: 'Enviar novo vídeo' }}
        />
      )}

      {!loading && !error && data && data.items.length === 0 && (
        <EmptyState
          title="Sem análises por aqui ainda"
          description="Envie seu primeiro vídeo para ver o diagnóstico biomecânico e acompanhar sua evolução."
          action={
            <Button onClick={() => navigate('/upload')}>
              Enviar primeiro vídeo
            </Button>
          }
        />
      )}

      {!loading && !error && data && data.items.length > 0 && (
        <>
          <HistoricoHero
            sparkPoints={sparkPoints}
            avg={avg}
            trendDelta={trendDelta}
          />

          <section className="historico-filters" aria-label="Filtros do histórico">
            <FilterChipGroup
              label="Período"
              options={PERIODO_FILTERS}
              value={periodo}
              onChange={setPeriodo}
            />
            <FilterChipGroup
              label="Status"
              options={STATUS_FILTERS}
              value={statusFilter}
              onChange={setStatusFilter}
            />
          </section>

          {filteredOutAll ? (
            <EmptyState
              title="Nenhuma análise nesta página com os filtros atuais"
              description="Tente ajustar o período ou o status, ou navegue para outras páginas do histórico."
              action={
                filtersActive ? (
                  <Button
                    variant="secondary"
                    onClick={() => {
                      updateParams((p) => {
                        p.delete('periodo')
                        p.delete('status')
                        p.delete('page')
                      })
                    }}
                  >
                    Limpar filtros
                  </Button>
                ) : null
              }
            />
          ) : (
            <ul className="historico-cards" aria-label="Sessões de análise">
              {visibleItems.map((item, idx) => {
                const reason = errorReasonForStatus(item.status)
                const expanded = selectedErrorId === item.id
                return (
                  <HistoricoCard
                    key={item.id}
                    item={item}
                    reason={reason}
                    expanded={expanded}
                    enterIndex={idx}
                    onClick={() => handleItemClick(item)}
                  />
                )
              })}
            </ul>
          )}

          <nav
            className="historico-pagination"
            aria-label="Paginação do histórico"
          >
            <Button
              variant="ghost"
              size="md"
              onClick={() => goToPage(page - 1)}
              disabled={!hasPrev}
              aria-label="Página anterior"
              aria-disabled={!hasPrev}
            >
              <span aria-hidden="true">←</span> Anterior
            </Button>
            <span className="historico-pagination-info" aria-live="polite">
              Página {page} de {pages}
            </span>
            <Button
              variant="ghost"
              size="md"
              onClick={() => goToPage(page + 1)}
              disabled={!hasNext}
              aria-label="Próxima página"
              aria-disabled={!hasNext}
            >
              Próxima <span aria-hidden="true">→</span>
            </Button>
          </nav>
        </>
      )}
    </main>
  )
}

interface HistoricoHeroProps {
  sparkPoints: ReturnType<typeof sparklinePoints>
  avg: number | null
  trendDelta: number | null
}

function HistoricoHero({ sparkPoints, avg, trendDelta }: HistoricoHeroProps) {
  const direction = trendDirection(trendDelta)
  const trendClass =
    direction === 'up'
      ? 'historico-hero-trend-up'
      : direction === 'down'
        ? 'historico-hero-trend-down'
        : 'historico-hero-trend-flat'
  const trendArrow = direction === 'up' ? '↑' : direction === 'down' ? '↓' : '→'

  return (
    <Card className="historico-hero">
      <div className="historico-hero-stats">
        <p className="historico-hero-label">Média desta página</p>
        <p className="historico-hero-value">
          <span className="historico-hero-number">{formatNotaAverage(avg)}</span>
          <span className="historico-hero-suffix">/10</span>
        </p>
        {trendDelta !== null && sparkPoints.length >= 2 ? (
          <p className={`historico-hero-trend ${trendClass}`}>
            <span aria-hidden="true">{trendArrow}</span>{' '}
            {formatTrendDelta(trendDelta)} vs sessões anteriores
          </p>
        ) : (
          <p className="historico-hero-trend historico-hero-trend-empty">
            Mais sessões trarão tendências comparativas.
          </p>
        )}
      </div>
      <div className="historico-hero-spark">
        <Sparkline points={sparkPoints} />
      </div>
    </Card>
  )
}

interface FilterChipGroupProps<T extends string> {
  label: string
  options: readonly { key: T; label: string }[]
  value: T
  onChange: (next: T) => void
}

function FilterChipGroup<T extends string>({
  label,
  options,
  value,
  onChange,
}: FilterChipGroupProps<T>) {
  return (
    <div className="historico-filter-group" role="group" aria-label={label}>
      <span className="historico-filter-label">{label}</span>
      <div
        className="historico-filter-chips"
        role="tablist"
        aria-label={label}
      >
        {options.map((opt) => {
          const active = opt.key === value
          return (
            <button
              key={opt.key}
              type="button"
              role="tab"
              aria-selected={active}
              className={`historico-chip${active ? ' historico-chip-active' : ''}`}
              onClick={() => onChange(opt.key)}
            >
              <Badge variant={active ? 'success' : 'neutral'}>{opt.label}</Badge>
            </button>
          )
        })}
      </div>
    </div>
  )
}

interface HistoricoCardProps {
  item: HistoricoItem
  reason: string | null
  expanded: boolean
  enterIndex: number
  onClick: () => void
}

function HistoricoCard({
  item,
  reason,
  expanded,
  enterIndex,
  onClick,
}: HistoricoCardProps) {
  const badge = statusBadge(item.status)
  const clickable = isConcluido(item.status) || reason !== null

  return (
    <li
      className={`historico-card list-enter${clickable ? ' historico-card-clickable' : ''}`}
      style={{ ['--enter-index' as string]: enterIndex }}
    >
      <button
        type="button"
        className="historico-card-button"
        onClick={onClick}
        disabled={!clickable}
        aria-expanded={reason !== null ? expanded : undefined}
      >
        <div className="historico-card-row historico-card-row-top">
          <span className="historico-card-date">
            {formatCriadoEm(item.criado_em)}
          </span>
          <span className={`historico-badge ${badge.className}`}>
            {badge.label}
          </span>
        </div>
        <div className="historico-card-row historico-card-row-bottom">
          <span className="historico-card-pace">
            <span className="historico-card-meta-label">Pace</span>
            {formatPaceMinKm(item.pace_min_km)}
          </span>
          <span className="historico-card-nota">
            <span className="historico-card-meta-label">Nota</span>
            <span className="historico-card-nota-value">
              {isConcluido(item.status) ? formatNotaGeral(item.nota_geral) : '—'}
            </span>
          </span>
        </div>
      </button>
      {reason && expanded && (
        <p className="historico-card-reason" role="status">
          {reason}
        </p>
      )}
    </li>
  )
}
