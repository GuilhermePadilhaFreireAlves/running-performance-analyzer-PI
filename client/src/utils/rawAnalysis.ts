// Pure helpers para a tela de dados biomecânicos brutos (US-026).
//
// Monta séries temporais por frame para plotagem com Recharts e o
// shape para visualização de simetria esq/dir. Não toca o DOM — Vitest
// roda em ambiente Node.

import type { RawFrame, SimetriaRawResponse } from '../api/analysis'

// Convenção: backend persiste joelho como ângulo interno (perna
// estendida = 180°). A UI do usuário mostra flexão = 180 - interno,
// alinhada com AnalysisPage / analysisDisplay.ts.
export const flexaoFromInterno = (valor: number): number => 180 - valor

export interface SeriesConfig {
  // Chave na série de cada frame (ex: 'angulo_joelho_esq').
  key: string
  // Rótulo exibido na legenda e tooltip.
  label: string
  // Cor estável da linha.
  color: string
  // Transformação opcional do valor por frame (ex: interno → flexão).
  transform?: (valor: number) => number
}

export interface ChartSpec {
  title: string
  unidade: string
  yLabel: string
  series: SeriesConfig[]
}

export const CHART_SPECS: readonly ChartSpec[] = [
  {
    title: 'Flexão do joelho por frame',
    unidade: '°',
    yLabel: 'Flexão (°)',
    series: [
      {
        key: 'angulo_joelho_esq',
        label: 'Joelho esq.',
        color: '#aa3bff',
        transform: flexaoFromInterno,
      },
      {
        key: 'angulo_joelho_dir',
        label: 'Joelho dir.',
        color: '#16a34a',
        transform: flexaoFromInterno,
      },
    ],
  },
  {
    title: 'Ângulo do cotovelo por frame',
    unidade: '°',
    yLabel: 'Ângulo (°)',
    series: [
      { key: 'angulo_cotovelo_esq', label: 'Cotovelo esq.', color: '#aa3bff' },
      { key: 'angulo_cotovelo_dir', label: 'Cotovelo dir.', color: '#16a34a' },
    ],
  },
  {
    title: 'Inclinação do tronco por frame',
    unidade: '°',
    yLabel: 'Inclinação (°)',
    series: [
      { key: 'inclinacao_tronco', label: 'Tronco', color: '#d69e2e' },
    ],
  },
  {
    title: 'Y do centro de massa por frame',
    unidade: 'px',
    yLabel: 'Y do CoM (px)',
    series: [{ key: 'y_com', label: 'Y do CoM', color: '#d0202f' }],
  },
]

export type FramePoint = {
  frame_idx: number
} & Record<string, number | null | undefined>

export function buildFramePoints(
  frames: readonly RawFrame[],
  specs: readonly ChartSpec[] = CHART_SPECS,
): FramePoint[] {
  // Pré-computa o conjunto de chaves de interesse + seus transforms para
  // evitar percorrer specs dentro do loop interno.
  const transforms = new Map<string, ((v: number) => number) | undefined>()
  for (const spec of specs) {
    for (const serie of spec.series) {
      transforms.set(serie.key, serie.transform)
    }
  }
  const result: FramePoint[] = []
  for (const frame of frames) {
    const point: FramePoint = { frame_idx: frame.frame_idx }
    for (const [key, transform] of transforms) {
      const raw = (frame as unknown as Record<string, number | null | undefined>)[key]
      if (raw === null || raw === undefined || Number.isNaN(raw)) {
        point[key] = null
      } else {
        point[key] = transform ? transform(raw) : raw
      }
    }
    result.push(point)
  }
  return result
}

export interface AsymmetryRow {
  key: string
  label: string
  valor: number | null
}

export const SIMETRIA_IDEAL_MAX_PCT = 10

export const ASYMMETRY_ROWS_META: readonly Omit<AsymmetryRow, 'valor'>[] = [
  { key: 'tcs', label: 'Tempo de contato (esq. vs. dir.)' },
  { key: 'joelho', label: 'Ângulo do joelho no contato inicial' },
  { key: 'oscilacao', label: 'Oscilação vertical do quadril' },
]

export function buildAsymmetryRows(
  simetria: SimetriaRawResponse,
): AsymmetryRow[] {
  return ASYMMETRY_ROWS_META.map((meta) => ({
    ...meta,
    valor: readSimetriaValue(simetria, meta.key),
  }))
}

function readSimetriaValue(
  simetria: SimetriaRawResponse,
  key: string,
): number | null {
  if (key === 'tcs') return simetria.tcs
  if (key === 'joelho') return simetria.joelho
  if (key === 'oscilacao') return simetria.oscilacao
  return null
}

export function asymmetryBarPct(valor: number | null): number {
  if (valor === null || Number.isNaN(valor)) return 0
  const abs = Math.abs(valor)
  // Escala de 0 a 30% para preencher barra (acima disso, visualmente cheio).
  const pct = (abs / 30) * 100
  if (pct < 0) return 0
  if (pct > 100) return 100
  return pct
}

export function asymmetryStatus(valor: number | null): 'ok' | 'alerta' | 'nd' {
  if (valor === null || Number.isNaN(valor)) return 'nd'
  return Math.abs(valor) <= SIMETRIA_IDEAL_MAX_PCT ? 'ok' : 'alerta'
}

export function formatAsymmetry(valor: number | null): string {
  if (valor === null || Number.isNaN(valor)) return 'não disponível'
  return `${valor.toFixed(1)}%`
}

// Utilitário de tooltip: formata rótulo numérico com a unidade do gráfico.
export function formatChartValue(
  valor: number | string | null | undefined,
  unidade: string,
): string {
  if (valor === null || valor === undefined) return '—'
  const num = typeof valor === 'number' ? valor : Number(valor)
  if (Number.isNaN(num)) return '—'
  return `${num.toFixed(1)} ${unidade}`
}
