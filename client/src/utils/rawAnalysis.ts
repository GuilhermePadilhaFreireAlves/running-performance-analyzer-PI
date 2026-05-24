// Pure helpers para a tela de dados biomecânicos brutos (US-026, US-040).
//
// Monta séries temporais por frame para plotagem com Recharts e o
// shape para visualização de simetria esq/dir. Não toca o DOM — Vitest
// roda em ambiente Node.

import type { EventosRawResponse, RawFrame, SimetriaRawResponse } from '../api/analysis'

// Convenção: backend persiste joelho como ângulo interno (perna
// estendida = 180°). A UI do usuário mostra flexão = 180 - interno,
// alinhada com AnalysisPage / analysisDisplay.ts.
export const flexaoFromInterno = (valor: number): number => 180 - valor

// Paleta Okabe-Ito (color-blind-friendly) usada nos charts e tabela:
// preserva contraste em protanopia/deuteranopia e em escala de cinza.
// Fonte: Okabe & Ito (2002); mapeamento do PRD seção 10: verde =
// "esq" (bluish green) e laranja = "dir" (vermillion).
export const OKABE_ITO = {
  bluishGreen: '#009E73',
  vermillion: '#D55E00',
  blue: '#0072B2',
  reddishPurple: '#CC79A7',
  orange: '#E69F00',
  skyBlue: '#56B4E9',
  yellow: '#F0E442',
} as const

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

export type ChartKey = 'joelho' | 'cotovelo' | 'tronco' | 'y_com'

export interface ChartSpec {
  chartKey: ChartKey
  title: string
  shortLabel: string
  unidade: string
  yLabel: string
  series: SeriesConfig[]
}

export const CHART_SPECS: readonly ChartSpec[] = [
  {
    chartKey: 'joelho',
    title: 'Flexão do joelho por frame',
    shortLabel: 'Joelho',
    unidade: '°',
    yLabel: 'Flexão (°)',
    series: [
      {
        key: 'angulo_joelho_esq',
        label: 'Joelho esq.',
        color: OKABE_ITO.bluishGreen,
        transform: flexaoFromInterno,
      },
      {
        key: 'angulo_joelho_dir',
        label: 'Joelho dir.',
        color: OKABE_ITO.vermillion,
        transform: flexaoFromInterno,
      },
    ],
  },
  {
    chartKey: 'cotovelo',
    title: 'Ângulo do cotovelo por frame',
    shortLabel: 'Cotovelo',
    unidade: '°',
    yLabel: 'Ângulo (°)',
    series: [
      {
        key: 'angulo_cotovelo_esq',
        label: 'Cotovelo esq.',
        color: OKABE_ITO.bluishGreen,
      },
      {
        key: 'angulo_cotovelo_dir',
        label: 'Cotovelo dir.',
        color: OKABE_ITO.vermillion,
      },
    ],
  },
  {
    chartKey: 'tronco',
    title: 'Inclinação do tronco por frame',
    shortLabel: 'Tronco',
    unidade: '°',
    yLabel: 'Inclinação (°)',
    series: [
      {
        key: 'inclinacao_tronco',
        label: 'Tronco',
        color: OKABE_ITO.blue,
      },
    ],
  },
  {
    chartKey: 'y_com',
    title: 'Y do centro de massa por frame',
    shortLabel: 'Y CoM',
    unidade: 'px',
    yLabel: 'Y do CoM (px)',
    series: [
      {
        key: 'y_com',
        label: 'Y do CoM',
        color: OKABE_ITO.reddishPurple,
      },
    ],
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

// --------------------------------------------------------------------------
// Faixas ideais por métrica (PRD Seção 9) — replica `biomechanics/recomendacoes.py`
// só para destacar visualmente frames fora do ideal. Valores já convertidos
// para a convenção mostrada ao usuário (flexão para o joelho; ângulo direto
// para cotovelo; inclinação para tronco).
// --------------------------------------------------------------------------
export interface FaixaIdeal {
  min: number
  max: number
}

export const FAIXAS_IDEAIS: Record<'joelho' | 'cotovelo' | 'tronco', FaixaIdeal> = {
  joelho: { min: 15, max: 25 },
  cotovelo: { min: 70, max: 110 },
  tronco: { min: 4, max: 8 },
}

export type MetricaFrameKey =
  | 'angulo_joelho_esq'
  | 'angulo_joelho_dir'
  | 'angulo_cotovelo_esq'
  | 'angulo_cotovelo_dir'
  | 'inclinacao_tronco'

const METRIC_TO_FAIXA: Record<MetricaFrameKey, keyof typeof FAIXAS_IDEAIS> = {
  angulo_joelho_esq: 'joelho',
  angulo_joelho_dir: 'joelho',
  angulo_cotovelo_esq: 'cotovelo',
  angulo_cotovelo_dir: 'cotovelo',
  inclinacao_tronco: 'tronco',
}

// Retorna true quando o valor (já no espaço da UI: flexão para joelho) está
// fora da faixa ideal. null/NaN → false (não destaca).
export function isValueOutOfRange(
  valor: number | null | undefined,
  metrica: MetricaFrameKey,
): boolean {
  if (valor === null || valor === undefined || Number.isNaN(valor)) return false
  const faixa = FAIXAS_IDEAIS[METRIC_TO_FAIXA[metrica]]
  return valor < faixa.min || valor > faixa.max
}

// Um frame é "fora do ideal" quando qualquer métrica disponível está fora
// da faixa — serve para destacar a linha inteira na tabela densa.
export function isFrameOutOfRange(point: FramePoint): boolean {
  const keys: MetricaFrameKey[] = [
    'angulo_joelho_esq',
    'angulo_joelho_dir',
    'angulo_cotovelo_esq',
    'angulo_cotovelo_dir',
    'inclinacao_tronco',
  ]
  for (const key of keys) {
    if (isValueOutOfRange(point[key] as number | null | undefined, key)) {
      return true
    }
  }
  return false
}

// --------------------------------------------------------------------------
// CSV export — gera o blob client-side (sem chamada à API). Inclui a coluna
// frame_idx + as mesmas métricas exibidas na tabela densa, com `y_com` em
// pixels e ângulos convertidos para a convenção visual. Null vira string
// vazia (padrão RFC 4180 para células sem valor).
// --------------------------------------------------------------------------
export const CSV_COLUMNS: readonly {
  key: keyof FramePoint | 'frame_idx'
  label: string
  decimals: number
}[] = [
  { key: 'frame_idx', label: 'frame_idx', decimals: 0 },
  { key: 'angulo_joelho_esq', label: 'flexao_joelho_esq_graus', decimals: 1 },
  { key: 'angulo_joelho_dir', label: 'flexao_joelho_dir_graus', decimals: 1 },
  { key: 'angulo_cotovelo_esq', label: 'angulo_cotovelo_esq_graus', decimals: 1 },
  { key: 'angulo_cotovelo_dir', label: 'angulo_cotovelo_dir_graus', decimals: 1 },
  { key: 'inclinacao_tronco', label: 'inclinacao_tronco_graus', decimals: 1 },
  { key: 'y_com', label: 'y_com_px', decimals: 1 },
]

export function buildCsv(points: readonly FramePoint[]): string {
  const header = CSV_COLUMNS.map((c) => c.label).join(',')
  const rows: string[] = [header]
  for (const point of points) {
    const cells: string[] = []
    for (const column of CSV_COLUMNS) {
      const raw = point[column.key]
      if (raw === null || raw === undefined || Number.isNaN(raw)) {
        cells.push('')
        continue
      }
      const num = typeof raw === 'number' ? raw : Number(raw)
      if (Number.isNaN(num)) {
        cells.push('')
        continue
      }
      cells.push(column.decimals === 0 ? String(num) : num.toFixed(column.decimals))
    }
    rows.push(cells.join(','))
  }
  return rows.join('\n')
}

export function buildCsvFilename(sessaoId: string | number): string {
  return `stride-analise-${sessaoId}-frames.csv`
}

// --------------------------------------------------------------------------
// Gráficos de eventos por passada (TCS, overstriding, cadência instantânea).
// Cada ponto representa um evento esparso (contato/passada) na timeline,
// não um frame contínuo.
// --------------------------------------------------------------------------

export type EventChartKey = 'tcs' | 'overstriding' | 'cadencia'

export interface EventChartSeries {
  key: string
  label: string
  color: string
}

export interface EventChartSpec {
  chartKey: EventChartKey
  title: string
  unidade: string
  yLabel: string
  series: readonly EventChartSeries[]
  valorKey: string
}

export const EVENT_CHART_SPECS: readonly EventChartSpec[] = [
  {
    chartKey: 'tcs',
    title: 'Tempo de contato por passada',
    unidade: 'ms',
    yLabel: 'TCS (ms)',
    series: [
      { key: 'tcs_esq', label: 'TCS esq.', color: OKABE_ITO.bluishGreen },
      { key: 'tcs_dir', label: 'TCS dir.', color: OKABE_ITO.vermillion },
    ],
    valorKey: 'tcs_ms',
  },
  {
    chartKey: 'overstriding',
    title: 'Overstriding no contato inicial por passada',
    unidade: 'cm',
    yLabel: 'Overstriding (cm)',
    series: [
      { key: 'overstriding_esq', label: 'Overstriding esq.', color: OKABE_ITO.bluishGreen },
      { key: 'overstriding_dir', label: 'Overstriding dir.', color: OKABE_ITO.vermillion },
    ],
    valorKey: 'overstriding_cm',
  },
  {
    chartKey: 'cadencia',
    title: 'Cadência instantânea por passada',
    unidade: 'spm',
    yLabel: 'Cadência (spm)',
    series: [
      { key: 'cadencia', label: 'Cadência inst.', color: OKABE_ITO.orange },
    ],
    valorKey: 'cadencia_spm',
  },
]

// Ponto na timeline de eventos: frame_idx + um valor por série (null onde
// a série não tem evento naquele frame).
export interface EventTimelinePoint {
  frame_idx: number
  [key: string]: number | null
}

// Mescla todos os frame_idx de todas as séries num array ordenado e preenche
// null onde uma série não tem evento. Permite usar LineChart com connectNulls
// para ligar apenas os pontos da mesma perna sem misturar esq/dir.
export function buildEventTimeline(
  eventos: EventosRawResponse,
  spec: EventChartSpec,
): EventTimelinePoint[] {
  const allFrames = new Set<number>()
  const seriesData = new Map<string, Map<number, number>>()

  for (const serie of spec.series) {
    const arr = (eventos as unknown as Record<string, Record<string, number>[]>)[serie.key] ?? []
    const data = new Map<number, number>()
    for (const e of arr) {
      const fi = e['frame_idx']
      const val = e[spec.valorKey]
      if (fi !== undefined && val !== undefined) {
        allFrames.add(fi)
        data.set(fi, val)
      }
    }
    seriesData.set(serie.key, data)
  }

  return Array.from(allFrames)
    .sort((a, b) => a - b)
    .map((frame_idx) => {
      const point: EventTimelinePoint = { frame_idx }
      for (const serie of spec.series) {
        point[serie.key] = seriesData.get(serie.key)?.get(frame_idx) ?? null
      }
      return point
    })
}

export function hasEventos(eventos: EventosRawResponse): boolean {
  return (
    eventos.tcs_esq.length > 0 ||
    eventos.tcs_dir.length > 0 ||
    eventos.overstriding_esq.length > 0 ||
    eventos.overstriding_dir.length > 0 ||
    eventos.cadencia.length > 0
  )
}
