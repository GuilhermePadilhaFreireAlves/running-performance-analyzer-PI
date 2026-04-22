import { useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
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

export default function HistoricoPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const navigate = useNavigate()
  const page = parsePageParam(searchParams.get('page'))
  const [data, setData] = useState<HistoricoResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedErrorId, setSelectedErrorId] = useState<number | null>(null)

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
        setError(general ?? 'Não foi possível carregar o histórico.')
      })
      .finally(() => {
        if (cancelled) return
        setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [page])

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
    <main className="historico-container">
      <h1>Histórico de análises</h1>

      {loading && <p className="historico-loading">Carregando histórico…</p>}

      {error && !loading && (
        <p className="form-error">{error}</p>
      )}

      {!loading && !error && data && data.items.length === 0 && (
        <p className="historico-empty">
          Você ainda não tem análises concluídas.{' '}
          <Link to="/upload" className="historico-empty-link">
            Envie seu primeiro vídeo
          </Link>
          .
        </p>
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
            >
              ← Anterior
            </button>
            <span className="historico-pagination-info">
              Página {page} de {pages}
            </span>
            <button
              type="button"
              className="historico-pagination-button"
              onClick={() => goToPage(page + 1)}
              disabled={!hasNext}
            >
              Próxima →
            </button>
          </nav>
        </>
      )}
    </main>
  )
}
