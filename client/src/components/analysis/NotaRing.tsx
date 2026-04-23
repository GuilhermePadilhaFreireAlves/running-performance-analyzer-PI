/**
 * NotaRing — anel circular SVG que representa graficamente a nota geral no
 * hero do diagnóstico (US-039). O arco é preenchido proporcionalmente à nota
 * (0–10) e colorido por faixa: verde >= 7, âmbar 5–7, vermelho < 5. A nota
 * textual é renderizada no centro; o valor numérico é marcado com
 * `font-variant-numeric: tabular-nums` via CSS (`.analysis-ring-value`).
 */
import { formatNota, notaClassName } from '../../utils/analysisDisplay'

const SIZE = 180
const STROKE = 14
const RADIUS = (SIZE - STROKE) / 2
const CIRCUMFERENCE = 2 * Math.PI * RADIUS
const MAX_NOTA = 10

interface NotaRingProps {
  nota: number | null
  classification: string
}

function clampNota(nota: number | null): number {
  if (nota === null || Number.isNaN(nota)) return 0
  if (nota < 0) return 0
  if (nota > MAX_NOTA) return MAX_NOTA
  return nota
}

export function NotaRing({ nota, classification }: NotaRingProps) {
  const normalised = clampNota(nota)
  const fraction = normalised / MAX_NOTA
  const dashLength = CIRCUMFERENCE * fraction
  const dashGap = CIRCUMFERENCE - dashLength
  const colorClass = notaClassName(nota)

  return (
    <div className={`analysis-ring ${colorClass}`}>
      <svg
        className="analysis-ring-svg"
        viewBox={`0 0 ${SIZE} ${SIZE}`}
        width={SIZE}
        height={SIZE}
        role="img"
        aria-label={`Nota geral ${formatNota(nota)} de 10 — ${classification}`}
      >
        <circle
          className="analysis-ring-track"
          cx={SIZE / 2}
          cy={SIZE / 2}
          r={RADIUS}
          strokeWidth={STROKE}
          fill="none"
        />
        <circle
          className="analysis-ring-progress"
          cx={SIZE / 2}
          cy={SIZE / 2}
          r={RADIUS}
          strokeWidth={STROKE}
          strokeLinecap="round"
          fill="none"
          strokeDasharray={`${dashLength} ${dashGap}`}
          transform={`rotate(-90 ${SIZE / 2} ${SIZE / 2})`}
        />
      </svg>
      <div className="analysis-ring-text" aria-hidden="true">
        <span className="analysis-ring-value">{formatNota(nota)}</span>
        <span className="analysis-ring-max">/10</span>
      </div>
    </div>
  )
}
