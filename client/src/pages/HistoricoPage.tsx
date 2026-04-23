import { useCallback, useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import {
  getHistoricoRequest,
  type HistoricoItem,
  type HistoricoResponse,
} from '../api/historico'
import { extractApiError } from '../api/errors'
import {
  HISTORICO_PAGE_SIZE,
  errorReasonForStatus,
  formatCriadoEm,
  formatNotaGeral,
  formatPaceMinKm,
  isConcluido,
  parsePageParam,
  statusBadge,
  totalPages,
} from '../utils/historicoDisplay'
import { usePageTitle } from '../hooks/usePageTitle'
import { useToast } from '../context/ToastContext'
import { Button, EmptyState, ErrorState, LoadingState } from '../components/ui'

export default function HistoricoPage() {
  usePageTitle('Histórico')
  const [searchParams, setSearchParams] = useSearchParams()
  const navigate = useNavigate()
  const toast = useToast()
  const page = parsePageParam(searchParams.get('page'))
  const [data, setData] = useState<HistoricoResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedErrorId, setSelectedErrorId] = useState<number | null>(null)
  const [retryCount, setRetryCount] = useState(0)

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

  const handleRetry = useCallback(() => setRetryCount((c) => c + 1), [])

  const goToPage = (target: number) => {
    const next = new URLSearchParams(searchParams)
    next.set('page', target.toString())
    setSearchParams(next)
  }

  const handleItemClick = (item: HistoricoItem) => {
    if (isConcluido(item.status)) {
      navigate(`/analysis/${item.id}`)
      return
    }
    const reason = errorReasonForStatus(item.status)
    if (reason) {
      setSelectedErrorId((current) =>
        current === item.id ? null : item.id,
      )
    }
  }

  const pages = data ? totalPages(data.total, data.limit) : 1
  const hasPrev = page > 1
  const hasNext = data !== null && page < pages

  return (
    <main id="main" tabIndex={-1} className="historico-container">
      <h1>Histórico de análises</h1>

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
          <ul className="historico-list">
            {data.items.map((item) => {
              const badge = statusBadge(item.status)
              const reason = errorReasonForStatus(item.status)
              const clickable = isConcluido(item.status) || reason !== null
              const expanded = selectedErrorId === item.id
              return (
                <li
                  key={item.id}
                  className={`historico-item${clickable ? ' historico-item-clickable' : ''}`}
                >
                  <button
                    type="button"
                    className="historico-item-button"
                    onClick={() => handleItemClick(item)}
                    disabled={!clickable}
                    aria-expanded={reason !== null ? expanded : undefined}
                  >
                    <span className="historico-item-date">
                      {formatCriadoEm(item.criado_em)}
                    </span>
                    <span className="historico-item-pace">
                      Pace: {formatPaceMinKm(item.pace_min_km)}
                    </span>
                    <span className={`historico-item-badge ${badge.className}`}>
                      {badge.label}
                    </span>
                    <span className="historico-item-nota">
                      {isConcluido(item.status)
                        ? formatNotaGeral(item.nota_geral)
                        : '—'}
                    </span>
                  </button>
                  {reason && expanded && (
                    <p className="historico-item-reason">{reason}</p>
                  )}
                </li>
              )
            })}
          </ul>

          <nav
            className="historico-pagination"
            aria-label="Paginação do histórico"
          >
            <button
              type="button"
              className="historico-pagination-button"
              onClick={() => goToPage(page - 1)}
              disabled={!hasPrev}
              aria-label="Página anterior"
            >
              <span aria-hidden="true">←</span> Anterior
            </button>
            <span className="historico-pagination-info">
              Página {page} de {pages}
            </span>
            <button
              type="button"
              className="historico-pagination-button"
              onClick={() => goToPage(page + 1)}
              disabled={!hasNext}
              aria-label="Próxima página"
            >
              Próxima <span aria-hidden="true">→</span>
            </button>
          </nav>
        </>
      )}
    </main>
  )
}
