import {
  useCallback,
  useDeferredValue,
  useEffect,
  useMemo,
  useState,
} from 'react'
import { useNavigate, useParams } from 'react-router-dom'
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
  CSV_COLUMNS,
  asymmetryBarPct,
  asymmetryStatus,
  buildAsymmetryRows,
  buildCsv,
  buildCsvFilename,
  buildFramePoints,
  formatAsymmetry,
  formatChartValue,
  isFrameOutOfRange,
  isValueOutOfRange,
  SIMETRIA_IDEAL_MAX_PCT,
  type ChartKey,
  type ChartSpec,
  type FramePoint,
  type MetricaFrameKey,
} from '../utils/rawAnalysis'
import { usePageTitle } from '../hooks/usePageTitle'
import { useToast } from '../context/ToastContext'
import { Badge, Banner, Button, ErrorState, LoadingState } from '../components/ui'

type ChartFilter = 'todos' | ChartKey

const CHART_FILTERS: readonly { key: ChartFilter; label: string }[] = [
  { key: 'todos', label: 'Todos' },
  { key: 'joelho', label: 'Joelho' },
  { key: 'cotovelo', label: 'Cotovelo' },
  { key: 'tronco', label: 'Tronco' },
  { key: 'y_com', label: 'Y do CoM' },
]

const ROWS_PER_PAGE = 25

export default function AnalysisRawPage() {
  const { id } = useParams<{ id: string }>()
  usePageTitle(id ? `Dados técnicos #${id}` : 'Dados técnicos')
  const navigate = useNavigate()
  const toast = useToast()
  const [data, setData] = useState<AnalysisRawResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [retryCount, setRetryCount] = useState(0)
  const [filter, setFilter] = useState<ChartFilter>('todos')
  const [page, setPage] = useState(0)
  const deferredPage = useDeferredValue(page)

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
  }, [id, retryCount, toast])

  const handleRetry = useCallback(() => setRetryCount((c) => c + 1), [])

  const points = useMemo<FramePoint[]>(
    () => (data?.frames ? buildFramePoints(data.frames) : []),
    [data?.frames],
  )
  const asymmetryRows = useMemo(
    () => (data?.simetria ? buildAsymmetryRows(data.simetria) : []),
    [data?.simetria],
  )

  const visibleCharts = useMemo<readonly ChartSpec[]>(
    () =>
      filter === 'todos'
        ? CHART_SPECS
        : CHART_SPECS.filter((c) => c.chartKey === filter),
    [filter],
  )

  const totalPages = Math.max(1, Math.ceil(points.length / ROWS_PER_PAGE))
  const safePage = Math.min(deferredPage, totalPages - 1)
  const pageStart = safePage * ROWS_PER_PAGE
  const pageRows = useMemo(
    () => points.slice(pageStart, pageStart + ROWS_PER_PAGE),
    [points, pageStart],
  )

  const handleExportCsv = useCallback(() => {
    if (!id || points.length === 0) return
    const csv = buildCsv(points)
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = buildCsvFilename(id)
    document.body.appendChild(anchor)
    anchor.click()
    anchor.remove()
    URL.revokeObjectURL(url)
    toast.success('CSV exportado com sucesso.')
  }, [id, points, toast])

  if (!id) {
    return (
      <main id="main" tabIndex={-1} className="raw-container">
        <h1>Dados técnicos</h1>
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
      <main id="main" tabIndex={-1} className="raw-container">
        <h1>Dados técnicos</h1>
        <LoadingState variant="analysis-raw" label="Carregando séries por frame" />
      </main>
    )
  }

  if (error) {
    return (
      <main id="main" tabIndex={-1} className="raw-container">
        <h1>Dados técnicos</h1>
        <ErrorState
          message={error}
          onRetry={handleRetry}
          backTo={{ to: `/analysis/${id}`, label: 'Voltar ao diagnóstico' }}
        />
      </main>
    )
  }

  if (!data) return null

  if (data.erro) {
    return (
      <main id="main" tabIndex={-1} className="raw-container">
        <h1>Dados técnicos</h1>
        <ErrorState
          title="Não foi possível analisar este vídeo"
          message={data.erro}
          backTo={{ to: '/upload', label: 'Enviar novo vídeo' }}
        />
      </main>
    )
  }

  return (
    <main id="main" tabIndex={-1} className="raw-container">
      <nav className="raw-back" aria-label="Navegação secundária">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate(`/analysis/${id}`)}
        >
          <span aria-hidden="true">←</span> Voltar ao diagnóstico
        </Button>
      </nav>

      <header className="raw-header">
        <div>
          <h1>Dados técnicos</h1>
          <p className="raw-subtitle">
            Sessão #{id}
            {data.fps !== null && data.fps !== undefined && (
              <> • {data.fps.toFixed(1)} fps</>
            )}
            {' • '}
            {points.length} frames
          </p>
        </div>
        <Button
          variant="secondary"
          size="sm"
          onClick={handleExportCsv}
          disabled={points.length === 0}
        >
          Exportar CSV
        </Button>
      </header>

      <section className="raw-section" aria-labelledby="raw-charts-heading">
        <div className="raw-section-header">
          <h2 id="raw-charts-heading">Séries por frame</h2>
          <p className="raw-section-help">
            Esquerda em <span className="raw-legend-swatch raw-legend-esq" aria-hidden="true" /> verde,
            direita em <span className="raw-legend-swatch raw-legend-dir" aria-hidden="true" /> laranja
            — paleta acessível a daltonismo (Okabe-Ito).
          </p>
        </div>

        {points.length === 0 ? (
          <Banner variant="info">
            Não há dados por frame persistidos para esta sessão.
          </Banner>
        ) : (
          <>
            <div
              className="raw-filter-chips"
              role="tablist"
              aria-label="Filtrar por métrica"
            >
              {CHART_FILTERS.map((f) => {
                const active = filter === f.key
                return (
                  <button
                    key={f.key}
                    type="button"
                    role="tab"
                    aria-selected={active}
                    className={`raw-chip${active ? ' raw-chip-active' : ''}`}
                    onClick={() => setFilter(f.key)}
                  >
                    <Badge variant={active ? 'success' : 'neutral'}>
                      {f.label}
                    </Badge>
                  </button>
                )
              })}
            </div>

            <div
              className={`raw-chart-grid${
                visibleCharts.length === 1 ? ' raw-chart-grid-single' : ''
              }`}
            >
              {visibleCharts.map((spec) => (
                <RawChart key={spec.chartKey} spec={spec} points={points} />
              ))}
            </div>
          </>
        )}
      </section>

      <section className="raw-section" aria-labelledby="raw-asymmetry-heading">
        <h2 id="raw-asymmetry-heading">Simetria esquerda ↔ direita</h2>
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

      {points.length > 0 && (
        <section className="raw-section" aria-labelledby="raw-table-heading">
          <h2 id="raw-table-heading">Tabela por frame</h2>
          <p className="raw-section-help">
            Linhas com destaque representam frames fora da faixa ideal em pelo
            menos uma métrica.
          </p>
          <div className="raw-table-wrap" role="region" aria-label="Tabela de métricas por frame" tabIndex={0}>
            <table className="raw-table">
              <thead>
                <tr>
                  {CSV_COLUMNS.map((c) => (
                    <th key={c.label} scope="col">
                      {columnHeader(c.label)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {pageRows.map((point) => {
                  const outlier = isFrameOutOfRange(point)
                  return (
                    <tr
                      key={point.frame_idx}
                      className={outlier ? 'raw-table-outlier' : undefined}
                    >
                      {CSV_COLUMNS.map((c) => (
                        <td key={c.label} className="raw-table-cell">
                          {renderCell(point, c.key, c.decimals)}
                        </td>
                      ))}
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          <nav className="raw-pagination" aria-label="Paginação da tabela">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={safePage <= 0}
              aria-label="Página anterior"
            >
              ← Anterior
            </Button>
            <span className="raw-pagination-status" aria-live="polite">
              Página {safePage + 1} de {totalPages}
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
              disabled={safePage >= totalPages - 1}
              aria-label="Próxima página"
            >
              Próxima →
            </Button>
          </nav>
        </section>
      )}

      <footer className="raw-footer">
        <Button
          variant="secondary"
          size="md"
          onClick={() => navigate(`/analysis/${id}`)}
        >
          Voltar ao diagnóstico
        </Button>
      </footer>
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
        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={points} margin={{ top: 8, right: 16, left: 8, bottom: 24 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis
              dataKey="frame_idx"
              stroke="var(--text-muted)"
              tick={{ fontSize: 11 }}
              label={{
                value: 'Frame',
                position: 'insideBottom',
                offset: -8,
                fill: 'var(--text-muted)',
                fontSize: 12,
              }}
            />
            <YAxis
              stroke="var(--text-muted)"
              tick={{ fontSize: 11 }}
              label={{
                value: spec.yLabel,
                angle: -90,
                position: 'insideLeft',
                offset: 12,
                fill: 'var(--text-muted)',
                fontSize: 12,
              }}
            />
            <Tooltip
              contentStyle={{
                background: 'var(--surface)',
                border: '1px solid var(--border)',
                borderRadius: 8,
                fontSize: 12,
              }}
              labelFormatter={(label) => `Frame ${label}`}
              formatter={(value) => formatChartValue(value as number | null, spec.unidade)}
            />
            <Legend verticalAlign="top" height={28} wrapperStyle={{ fontSize: 12 }} />
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

function columnHeader(label: string): string {
  switch (label) {
    case 'frame_idx':
      return 'Frame'
    case 'flexao_joelho_esq_graus':
      return 'Joelho esq. (°)'
    case 'flexao_joelho_dir_graus':
      return 'Joelho dir. (°)'
    case 'angulo_cotovelo_esq_graus':
      return 'Cotovelo esq. (°)'
    case 'angulo_cotovelo_dir_graus':
      return 'Cotovelo dir. (°)'
    case 'inclinacao_tronco_graus':
      return 'Tronco (°)'
    case 'y_com_px':
      return 'Y CoM (px)'
    default:
      return label
  }
}

function renderCell(
  point: FramePoint,
  key: keyof FramePoint | 'frame_idx',
  decimals: number,
) {
  const raw = point[key]
  if (raw === null || raw === undefined || Number.isNaN(raw)) {
    return <span className="raw-table-null">—</span>
  }
  const num = typeof raw === 'number' ? raw : Number(raw)
  if (Number.isNaN(num)) return <span className="raw-table-null">—</span>
  const text = decimals === 0 ? String(num) : num.toFixed(decimals)
  const highlight =
    key !== 'frame_idx' &&
    key !== 'y_com' &&
    isValueOutOfRange(num, key as MetricaFrameKey)
  return (
    <span className={highlight ? 'raw-table-cell-warn' : undefined}>{text}</span>
  )
}
