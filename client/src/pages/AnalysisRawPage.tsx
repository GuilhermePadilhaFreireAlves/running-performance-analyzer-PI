import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import {
  getRawAnalysisRequest,
  type AnalysisRawResponse,
} from '../api/analysis'
import { extractApiError } from '../api/errors'
import {
  CHART_SPECS,
  asymmetryBarPct,
  asymmetryStatus,
  buildAsymmetryRows,
  buildFramePoints,
  formatAsymmetry,
  formatChartValue,
  SIMETRIA_IDEAL_MAX_PCT,
  type ChartSpec,
  type FramePoint,
} from '../utils/rawAnalysis'
import { usePageTitle } from '../hooks/usePageTitle'
import { useToast } from '../context/ToastContext'
import { Banner } from '../components/ui'

export default function AnalysisRawPage() {
  usePageTitle('Dados técnicos')
  const { id } = useParams<{ id: string }>()
  const toast = useToast()
  const [data, setData] = useState<AnalysisRawResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    let cancelled = false
    setLoading(true)
    setError(null)
    setData(null)
    getRawAnalysisRequest(id)
      .then((resp) => {
        if (cancelled) return
        setData(resp)
      })
      .catch((err: unknown) => {
        if (cancelled) return
        const { general } = extractApiError(err)
        const message = general ?? 'Não foi possível carregar os dados brutos.'
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
  }, [id, toast])

  const points = useMemo<FramePoint[]>(
    () => (data?.frames ? buildFramePoints(data.frames) : []),
    [data?.frames],
  )
  const asymmetryRows = useMemo(
    () => (data?.simetria ? buildAsymmetryRows(data.simetria) : []),
    [data?.simetria],
  )

  if (!id) {
    return (
      <main id="main" tabIndex={-1} className="analysis-container">
        <h1>Dados biomecânicos brutos</h1>
        <Banner variant="danger" assertive>
          Identificador de análise ausente.
        </Banner>
      </main>
    )
  }

  if (loading) {
    return (
      <main id="main" tabIndex={-1} className="analysis-container">
        <h1>Dados biomecânicos brutos</h1>
        <p className="analysis-loading">Carregando séries por frame…</p>
      </main>
    )
  }

  if (error) {
    return (
      <main id="main" tabIndex={-1} className="analysis-container">
        <h1>Dados biomecânicos brutos</h1>
        <p className="analysis-empty">Não foi possível carregar. Tente novamente.</p>
        <p className="analysis-actions">
          <Link to={`/analysis/${id}`} className="analysis-primary-link">
            Voltar ao diagnóstico simplificado
          </Link>
        </p>
      </main>
    )
  }

  if (!data) return null

  if (data.erro) {
    return (
      <main id="main" tabIndex={-1} className="analysis-container">
        <h1>Dados biomecânicos brutos</h1>
        <Banner variant="danger" assertive>
          {data.erro}
        </Banner>
        <p className="analysis-actions">
          <Link to="/upload" className="analysis-primary-link">
            Enviar novo vídeo
          </Link>
        </p>
      </main>
    )
  }

  return (
    <main id="main" tabIndex={-1} className="analysis-container">
      <h1>Dados biomecânicos brutos</h1>

      <p className="analysis-feedback">
        Sessão #{id}
        {data.fps !== null && data.fps !== undefined && (
          <> • {data.fps.toFixed(1)} fps</>
        )}
        {' • '}
        {points.length} frames
      </p>

      <section className="analysis-section">
        <h2>Séries por frame</h2>
        {points.length === 0 ? (
          <p className="analysis-empty">
            Não há dados por frame persistidos para esta sessão.
          </p>
        ) : (
          <div className="raw-chart-grid">
            {CHART_SPECS.map((spec) => (
              <RawChart key={spec.title} spec={spec} points={points} />
            ))}
          </div>
        )}
      </section>

      <section className="analysis-section">
        <h2>Simetria esquerda ↔ direita</h2>
        <p className="raw-asymmetry-help">
          Referência: assimetria acima de {SIMETRIA_IDEAL_MAX_PCT}% é preditor
          de risco de lesão.
        </p>
        <ul className="raw-asymmetry-list">
          {asymmetryRows.map((row) => {
            const status = asymmetryStatus(row.valor)
            return (
              <li key={row.key} className="raw-asymmetry-row">
                <div className="raw-asymmetry-header">
                  <span className="raw-asymmetry-label">{row.label}</span>
                  <span
                    className={`raw-asymmetry-value raw-asymmetry-${status}`}
                  >
                    {formatAsymmetry(row.valor)}
                  </span>
                </div>
                <div
                  className="raw-asymmetry-bar"
                  role="img"
                  aria-label={`Assimetria ${row.label}: ${formatAsymmetry(row.valor)}`}
                >
                  <div
                    className={`raw-asymmetry-bar-fill raw-asymmetry-${status}`}
                    style={{ width: `${asymmetryBarPct(row.valor)}%` }}
                  />
                  <div
                    className="raw-asymmetry-threshold"
                    style={{ left: `${(SIMETRIA_IDEAL_MAX_PCT / 30) * 100}%` }}
                    aria-hidden="true"
                  />
                </div>
              </li>
            )
          })}
        </ul>
      </section>

      <p className="analysis-actions">
        <Link to={`/analysis/${id}`} className="analysis-raw-link">
          ← Voltar ao diagnóstico simplificado
        </Link>
      </p>
    </main>
  )
}

interface RawChartProps {
  spec: ChartSpec
  points: FramePoint[]
}

function RawChart({ spec, points }: RawChartProps) {
  return (
    <article className="raw-chart">
      <h3 className="raw-chart-title">{spec.title}</h3>
      <div className="raw-chart-body">
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={points} margin={{ top: 8, right: 12, left: 8, bottom: 24 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis
              dataKey="frame_idx"
              stroke="var(--text)"
              label={{
                value: 'Frame',
                position: 'insideBottom',
                offset: -8,
                fill: 'var(--text)',
                fontSize: 12,
              }}
            />
            <YAxis
              stroke="var(--text)"
              label={{
                value: spec.yLabel,
                angle: -90,
                position: 'insideLeft',
                offset: 12,
                fill: 'var(--text)',
                fontSize: 12,
              }}
            />
            <Tooltip
              labelFormatter={(label) => `Frame ${label}`}
              formatter={(value) => formatChartValue(value as number | null, spec.unidade)}
            />
            <Legend verticalAlign="top" height={24} />
            {spec.series.map((serie) => (
              <Line
                key={serie.key}
                type="monotone"
                dataKey={serie.key}
                name={serie.label}
                stroke={serie.color}
                dot={false}
                strokeWidth={2}
                connectNulls={false}
                isAnimationActive={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </article>
  )
}
