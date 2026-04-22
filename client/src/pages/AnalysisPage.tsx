import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  getSimpleAnalysisRequest,
  type AnalysisSimpleResponse,
} from '../api/analysis'
import { extractApiError } from '../api/errors'
import {
  SEVERIDADE_ATENCAO,
  SEVERIDADE_CRITICO,
  SEVERIDADE_INFORMATIVO,
  SEVERIDADE_ORDEM,
  buildMetricasVisuais,
  formatNota,
  groupBySeveridade,
  notaClassName,
  severidadeDisplay,
} from '../utils/analysisDisplay'

export default function AnalysisPage() {
  const { id } = useParams<{ id: string }>()
  const [data, setData] = useState<AnalysisSimpleResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    let cancelled = false
    setLoading(true)
    setError(null)
    setData(null)
    getSimpleAnalysisRequest(id)
      .then((resp) => {
        if (cancelled) return
        setData(resp)
      })
      .catch((err: unknown) => {
        if (cancelled) return
        const { general } = extractApiError(err)
        setError(general ?? 'Não foi possível carregar a análise.')
      })
      .finally(() => {
        if (cancelled) return
        setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [id])

  if (!id) {
    return (
      <main className="analysis-container">
        <h1>Diagnóstico</h1>
        <p className="form-error">Identificador de análise ausente.</p>
      </main>
    )
  }

  if (loading) {
    return (
      <main className="analysis-container">
        <h1>Diagnóstico</h1>
        <p className="analysis-loading">Carregando análise…</p>
      </main>
    )
  }

  if (error) {
    return (
      <main className="analysis-container">
        <h1>Diagnóstico</h1>
        <p className="form-error">{error}</p>
        <p>
          <Link to="/historico">Ver histórico de análises</Link>
        </p>
      </main>
    )
  }

  if (!data) return null

  if (data.erro) {
    return (
      <main className="analysis-container">
        <h1>Diagnóstico</h1>
        <p className="form-error">{data.erro}</p>
        <p className="analysis-actions">
          <Link to="/upload" className="analysis-primary-link">
            Enviar novo vídeo
          </Link>
        </p>
      </main>
    )
  }

  const visuais = buildMetricasVisuais(data.metricas_resumidas)
  const grupos = groupBySeveridade(data.recomendacoes)

  return (
    <main className="analysis-container">
      <h1>Diagnóstico</h1>

      <section className={`analysis-nota-card ${notaClassName(data.nota_geral)}`}>
        <span className="analysis-nota-label">Nota geral</span>
        <span className="analysis-nota-value">
          {formatNota(data.nota_geral)}
          <span className="analysis-nota-max">/10</span>
        </span>
      </section>

      {data.feedback_ia && (
        <p className="analysis-feedback">{data.feedback_ia}</p>
      )}

      {visuais.length > 0 && (
        <section className="analysis-section">
          <h2>Métricas principais</h2>
          <ul className="analysis-metric-list">
            {visuais.map((v) => (
              <li key={v.tipo} className="analysis-metric">
                <div className="analysis-metric-header">
                  <span className="analysis-metric-label">{v.config.label}</span>
                  <span className="analysis-metric-value">
                    {v.gauge.displayValue}
                  </span>
                </div>
                <div className="analysis-gauge">
                  <div
                    className="analysis-gauge-ideal"
                    style={{
                      left: `${v.gauge.idealLeftPct}%`,
                      width: `${v.gauge.idealWidthPct}%`,
                    }}
                    aria-hidden="true"
                  />
                  <div
                    className="analysis-gauge-marker"
                    style={{ left: `${v.gauge.markerPct}%` }}
                    aria-hidden="true"
                  />
                </div>
                <div className="analysis-gauge-range">
                  <span>
                    {v.config.chartMin}
                    {v.config.unidade}
                  </span>
                  <span className="analysis-gauge-ideal-label">
                    faixa ideal: {v.config.idealMin}–{v.config.idealMax}
                    {v.config.unidade}
                  </span>
                  <span>
                    {v.config.chartMax}
                    {v.config.unidade}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="analysis-section">
        <h2>Recomendações</h2>
        {data.recomendacoes.length === 0 ? (
          <p className="analysis-empty">
            Nenhuma recomendação gerada para esta sessão.
          </p>
        ) : (
          SEVERIDADE_ORDEM.map((sev) => {
            const lista = grupos[sev] ?? []
            if (lista.length === 0) return null
            const display = severidadeDisplay(sev)
            const titulo =
              sev === SEVERIDADE_CRITICO
                ? 'Pontos críticos'
                : sev === SEVERIDADE_ATENCAO
                  ? 'Pontos de atenção'
                  : sev === SEVERIDADE_INFORMATIVO
                    ? 'Já está dentro do ideal'
                    : display.label
            return (
              <div key={sev} className="analysis-severity-group">
                <h3 className={`analysis-severity-title ${display.className}`}>
                  {titulo}
                </h3>
                <ul className="analysis-card-list">
                  {lista.map((rec, idx) => (
                    <li
                      key={`${sev}-${idx}`}
                      className={`analysis-card ${display.className}`}
                    >
                      <span className="analysis-card-badge">
                        {display.label}
                      </span>
                      <strong className="analysis-card-title">
                        {rec.categoria}
                      </strong>
                      <p className="analysis-card-body">{rec.descricao}</p>
                    </li>
                  ))}
                </ul>
              </div>
            )
          })
        )}
      </section>

      <p className="analysis-actions">
        <Link
          to={`/analysis/${id}/raw`}
          className="analysis-raw-link"
        >
          Ver dados técnicos →
        </Link>
      </p>
    </main>
  )
}
