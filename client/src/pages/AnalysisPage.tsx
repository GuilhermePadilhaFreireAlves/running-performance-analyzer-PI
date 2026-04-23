import { useCallback, useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
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
  groupBySeveridade,
  notaClassName,
  notaClassification,
  severidadeDisplay,
} from '../utils/analysisDisplay'
import { usePageTitle } from '../hooks/usePageTitle'
import { useToast } from '../context/ToastContext'
import { Banner, Button, ErrorState, LoadingState } from '../components/ui'
import { NotaRing } from '../components/analysis/NotaRing'
import { MetricIcon } from '../components/analysis/MetricIcon'

const SEVERIDADE_TITULOS: Record<string, string> = {
  [SEVERIDADE_CRITICO]: 'Pontos críticos',
  [SEVERIDADE_ATENCAO]: 'Pontos de atenção',
  [SEVERIDADE_INFORMATIVO]: 'Já está dentro do ideal',
}

export default function AnalysisPage() {
  const { id } = useParams<{ id: string }>()
  usePageTitle(id ? `Diagnóstico #${id}` : 'Diagnóstico')
  const navigate = useNavigate()
  const toast = useToast()
  const [data, setData] = useState<AnalysisSimpleResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [retryCount, setRetryCount] = useState(0)

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
        const message = general ?? 'Não foi possível carregar a análise.'
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
  }, [id, retryCount, toast])

  const handleRetry = useCallback(() => setRetryCount((c) => c + 1), [])

  if (!id) {
    return (
      <main id="main" tabIndex={-1} className="analysis-container">
        <h1>Diagnóstico</h1>
        <ErrorState
          title="Análise não encontrada"
          message="O identificador da análise não foi informado."
          backTo={{ to: '/historico', label: 'Voltar ao histórico' }}
        />
      </main>
    )
  }

  if (loading) {
    return (
      <main id="main" tabIndex={-1} className="analysis-container">
        <h1>Diagnóstico</h1>
        <LoadingState variant="analysis" label="Carregando análise" />
      </main>
    )
  }

  if (error) {
    return (
      <main id="main" tabIndex={-1} className="analysis-container">
        <h1>Diagnóstico</h1>
        <ErrorState
          message={error}
          onRetry={handleRetry}
          backTo={{ to: '/historico', label: 'Voltar ao histórico' }}
        />
      </main>
    )
  }

  if (!data) return null

  if (data.erro) {
    return (
      <main id="main" tabIndex={-1} className="analysis-container">
        <h1>Diagnóstico</h1>
        <ErrorState
          title="Não foi possível analisar este vídeo"
          message={data.erro}
          backTo={{ to: '/upload', label: 'Enviar novo vídeo' }}
        />
      </main>
    )
  }

  const visuais = buildMetricasVisuais(data.metricas_resumidas)
  const grupos = groupBySeveridade(data.recomendacoes)
  const classification = notaClassification(data.nota_geral)
  const notaColorClass = notaClassName(data.nota_geral)

  return (
    <main id="main" tabIndex={-1} className="analysis-container">
      <h1 className="visually-hidden">Diagnóstico #{id}</h1>

      <section
        className={`analysis-hero ${notaColorClass}`}
        aria-label="Nota geral"
      >
        <NotaRing nota={data.nota_geral} classification={classification} />
        <div className="analysis-hero-body">
          <p className="analysis-hero-label">Nota geral</p>
          <p className="analysis-hero-classification">{classification}</p>
          {data.feedback_ia && (
            <p className="analysis-hero-feedback">{data.feedback_ia}</p>
          )}
        </div>
      </section>

      {visuais.length > 0 && (
        <section className="analysis-section" aria-labelledby="analysis-metrics-title">
          <h2 id="analysis-metrics-title">Métricas principais</h2>
          <ul className="analysis-metric-grid">
            {visuais.map((v) => (
              <li key={v.tipo} className="analysis-metric-card">
                <div className="analysis-metric-card-header">
                  <span
                    className="analysis-metric-card-icon"
                    aria-hidden="true"
                  >
                    <MetricIcon name={v.config.icon} />
                  </span>
                  <span className="analysis-metric-card-label">
                    {v.config.label}
                  </span>
                </div>
                <p className="analysis-metric-card-value">
                  {v.gauge.displayValue}
                </p>
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
                    ideal {v.config.idealMin}–{v.config.idealMax}
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

      <section
        className="analysis-section"
        aria-labelledby="analysis-recomendacoes-title"
      >
        <h2
          id="analysis-recomendacoes-title"
          className="analysis-section-title"
        >
          Recomendações
        </h2>
        {data.recomendacoes.length === 0 ? (
          <Banner variant="success" title="Ótimo trabalho!">
            Sua corrida está dentro de todos os parâmetros ideais — continue
            assim.
          </Banner>
        ) : (
          SEVERIDADE_ORDEM.map((sev) => {
            const lista = grupos[sev] ?? []
            if (lista.length === 0) return null
            const display = severidadeDisplay(sev)
            const titulo = SEVERIDADE_TITULOS[sev] ?? display.label
            return (
              <div key={sev} className="analysis-severity-group">
                <h3 className={`analysis-severity-title ${display.className}`}>
                  <span
                    className="analysis-severity-icon"
                    aria-hidden="true"
                  >
                    {sev === SEVERIDADE_CRITICO
                      ? '!'
                      : sev === SEVERIDADE_ATENCAO
                        ? '!'
                        : '✓'}
                  </span>
                  {titulo}
                </h3>
                <ul className="analysis-card-list">
                  {lista.map((rec, idx) => (
                    <li
                      key={`${sev}-${idx}`}
                      className={`analysis-card list-enter ${display.className}`}
                      style={{ ['--enter-index' as string]: idx }}
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

      <footer className="analysis-footer">
        <Button
          variant="secondary"
          size="md"
          onClick={() => navigate('/historico')}
        >
          Voltar ao histórico
        </Button>
        <Button
          variant="primary"
          size="md"
          onClick={() => navigate(`/analysis/${id}/raw`)}
        >
          Ver dados técnicos
        </Button>
      </footer>
    </main>
  )
}
