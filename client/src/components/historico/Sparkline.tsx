/**
 * Sparkline — mini line chart for nota_geral evolution (US-041).
 *
 * Recharts-free SVG implementation: a single inline <svg> draws a smooth
 * polyline scaled to the container. Keeping it dependency-light avoids
 * Recharts in the histórico bundle and yields a sharper visual at small
 * sizes than the Recharts `<LineChart>` default.
 */
import type { SparklinePoint } from '../../utils/historicoDisplay'

export interface SparklineProps {
  points: readonly SparklinePoint[]
  width?: number
  height?: number
  ariaLabel?: string
}

const PADDING = 4
const Y_MIN = 0
const Y_MAX = 10

export function Sparkline({
  points,
  width = 220,
  height = 56,
  ariaLabel = 'Tendência da nota geral',
}: SparklineProps) {
  if (points.length === 0) {
    return (
      <div
        className="sparkline sparkline-empty"
        style={{ width, height }}
        aria-label="Sem dados de evolução"
        role="img"
      >
        <span className="sparkline-empty-text">sem dados</span>
      </div>
    )
  }

  if (points.length === 1) {
    const cx = width / 2
    const cy = scaleY(points[0].nota, height)
    return (
      <svg
        className="sparkline"
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label={ariaLabel}
      >
        <circle cx={cx} cy={cy} r={3} fill="var(--brand-500)" />
      </svg>
    )
  }

  const innerW = width - PADDING * 2
  const stepX = innerW / (points.length - 1)
  const coords = points.map((p, i) => ({
    x: PADDING + i * stepX,
    y: scaleY(p.nota, height),
  }))

  const linePath = coords
    .map((c, i) => `${i === 0 ? 'M' : 'L'} ${c.x.toFixed(2)} ${c.y.toFixed(2)}`)
    .join(' ')

  const areaPath = `${linePath} L ${coords[coords.length - 1].x.toFixed(2)} ${
    height - PADDING
  } L ${coords[0].x.toFixed(2)} ${height - PADDING} Z`

  const last = coords[coords.length - 1]

  return (
    <svg
      className="sparkline"
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      role="img"
      aria-label={ariaLabel}
    >
      <path d={areaPath} fill="var(--brand-100)" opacity={0.55} />
      <path
        d={linePath}
        stroke="var(--brand-500)"
        strokeWidth={1.75}
        fill="none"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx={last.x} cy={last.y} r={2.5} fill="var(--brand-500)" />
    </svg>
  )
}

function scaleY(value: number, height: number): number {
  const clamped = Math.min(Y_MAX, Math.max(Y_MIN, value))
  const ratio = (clamped - Y_MIN) / (Y_MAX - Y_MIN)
  // Invert Y for SVG coords (top=0).
  return height - PADDING - ratio * (height - PADDING * 2)
}
