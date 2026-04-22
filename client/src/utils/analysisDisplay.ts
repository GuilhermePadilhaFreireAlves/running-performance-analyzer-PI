// Pure helpers para a tela de diagnóstico simplificado (US-025).
//
// Mapeia métricas e severidades para rótulos amigáveis e computa a
// geometria dos gauges horizontais renderizados na UI. Não toca o DOM —
// Vitest roda em ambiente Node.

export const SEVERIDADE_INFORMATIVO = 'informativo'
export const SEVERIDADE_ATENCAO = 'atencao'
export const SEVERIDADE_CRITICO = 'critico'

export const SEVERIDADE_ORDEM: readonly string[] = [
  SEVERIDADE_CRITICO,
  SEVERIDADE_ATENCAO,
  SEVERIDADE_INFORMATIVO,
]

export interface SeveridadeDisplay {
  className: string
  label: string
}

const SEVERIDADE_DISPLAY: Record<string, SeveridadeDisplay> = {
  [SEVERIDADE_CRITICO]: { className: 'severity-critico', label: 'Crítico' },
  [SEVERIDADE_ATENCAO]: { className: 'severity-atencao', label: 'Atenção' },
  [SEVERIDADE_INFORMATIVO]: {
    className: 'severity-informativo',
    label: 'Dentro do ideal',
  },
}

export function severidadeDisplay(severidade: string): SeveridadeDisplay {
  return (
    SEVERIDADE_DISPLAY[severidade] ?? {
      className: 'severity-default',
      label: severidade,
    }
  )
}

export function notaClassName(nota: number | null): string {
  if (nota === null || Number.isNaN(nota)) return 'nota-neutral'
  if (nota >= 7) return 'nota-good'
  if (nota >= 4) return 'nota-ok'
  return 'nota-bad'
}

export function formatNota(nota: number | null): string {
  if (nota === null || Number.isNaN(nota)) return '—'
  return nota.toFixed(1)
}

export interface MetricaConfig {
  label: string
  unidade: string
  idealMin: number
  idealMax: number
  chartMin: number
  chartMax: number
  // Transformação opcional do valor armazenado em Metrica.valor antes
  // de renderizar no gauge (ex: joelho armazenado como ângulo interno,
  // exibido como flexão = 180 - interno).
  transform?: (valor: number) => number
  // Se true, usa |valor| para posicionamento no gauge (overstriding).
  usaAbs?: boolean
  // Formatação customizada do valor exibido em texto.
  formatar?: (valor: number) => string
}

const DEFAULT_FORMATTER = (valor: number): string => valor.toFixed(1)

const flexaoFromInterno = (valor: number): number => 180 - valor

export const METRIC_CONFIGS: Record<string, MetricaConfig> = {
  angulo_joelho_esq: {
    label: 'Flexão do joelho (esq.) no contato inicial',
    unidade: '°',
    idealMin: 15,
    idealMax: 25,
    chartMin: 0,
    chartMax: 60,
    transform: flexaoFromInterno,
  },
  angulo_joelho_dir: {
    label: 'Flexão do joelho (dir.) no contato inicial',
    unidade: '°',
    idealMin: 15,
    idealMax: 25,
    chartMin: 0,
    chartMax: 60,
    transform: flexaoFromInterno,
  },
  angulo_cotovelo_esq: {
    label: 'Ângulo do cotovelo (esq.)',
    unidade: '°',
    idealMin: 70,
    idealMax: 110,
    chartMin: 30,
    chartMax: 180,
  },
  angulo_cotovelo_dir: {
    label: 'Ângulo do cotovelo (dir.)',
    unidade: '°',
    idealMin: 70,
    idealMax: 110,
    chartMin: 30,
    chartMax: 180,
  },
  inclinacao_tronco: {
    label: 'Inclinação do tronco para frente',
    unidade: '°',
    idealMin: 4,
    idealMax: 8,
    chartMin: -5,
    chartMax: 20,
  },
  overstriding_esq: {
    label: 'Overstriding (esq.)',
    unidade: 'cm',
    idealMin: 0,
    idealMax: 5,
    chartMin: 0,
    chartMax: 25,
    usaAbs: true,
  },
  overstriding_dir: {
    label: 'Overstriding (dir.)',
    unidade: 'cm',
    idealMin: 0,
    idealMax: 5,
    chartMin: 0,
    chartMax: 25,
    usaAbs: true,
  },
  oscilacao_vertical: {
    label: 'Oscilação vertical do quadril',
    unidade: 'cm',
    idealMin: 5,
    idealMax: 10,
    chartMin: 0,
    chartMax: 20,
  },
  simetria_tcs: {
    label: 'Simetria — tempo de contato',
    unidade: '%',
    idealMin: 0,
    idealMax: 5,
    chartMin: 0,
    chartMax: 30,
  },
  simetria_joelho: {
    label: 'Simetria — ângulo do joelho',
    unidade: '%',
    idealMin: 0,
    idealMax: 5,
    chartMin: 0,
    chartMax: 30,
  },
  simetria_oscilacao: {
    label: 'Simetria — oscilação vertical',
    unidade: '%',
    idealMin: 0,
    idealMax: 5,
    chartMin: 0,
    chartMax: 30,
  },
  cadencia: {
    label: 'Cadência (informativo)',
    unidade: 'spm',
    idealMin: 170,
    idealMax: 185,
    chartMin: 140,
    chartMax: 210,
    formatar: (v) => v.toFixed(0),
  },
  tcs_esq: {
    label: 'Tempo de contato (esq., informativo)',
    unidade: 'ms',
    idealMin: 180,
    idealMax: 250,
    chartMin: 100,
    chartMax: 350,
    formatar: (v) => v.toFixed(0),
  },
  tcs_dir: {
    label: 'Tempo de contato (dir., informativo)',
    unidade: 'ms',
    idealMin: 180,
    idealMax: 250,
    chartMin: 100,
    chartMax: 350,
    formatar: (v) => v.toFixed(0),
  },
}

// Ordem de renderização dos gauges na UI.
export const METRIC_DISPLAY_ORDER: readonly string[] = [
  'angulo_joelho_esq',
  'angulo_joelho_dir',
  'inclinacao_tronco',
  'angulo_cotovelo_esq',
  'angulo_cotovelo_dir',
  'oscilacao_vertical',
  'overstriding_esq',
  'overstriding_dir',
  'simetria_tcs',
  'simetria_joelho',
  'simetria_oscilacao',
  'cadencia',
  'tcs_esq',
  'tcs_dir',
]

export interface GaugeGeometry {
  // Percentual [0, 100] da posição do marcador na barra.
  markerPct: number
  // Posição (esquerda) e largura em % da zona ideal realçada.
  idealLeftPct: number
  idealWidthPct: number
  // Valor exibido (já transformado e formatado com unidade).
  displayValue: string
}

function clampPct(pct: number): number {
  if (pct < 0) return 0
  if (pct > 100) return 100
  return pct
}

function valorParaPct(
  valor: number,
  chartMin: number,
  chartMax: number,
): number {
  if (chartMax <= chartMin) return 0
  return clampPct(((valor - chartMin) / (chartMax - chartMin)) * 100)
}

export function buildGaugeGeometry(
  config: MetricaConfig,
  valor: number,
): GaugeGeometry {
  const valorTransformado = config.transform ? config.transform(valor) : valor
  const valorParaMarker = config.usaAbs
    ? Math.abs(valorTransformado)
    : valorTransformado
  const markerPct = valorParaPct(
    valorParaMarker,
    config.chartMin,
    config.chartMax,
  )
  const idealLeft = valorParaPct(
    config.idealMin,
    config.chartMin,
    config.chartMax,
  )
  const idealRight = valorParaPct(
    config.idealMax,
    config.chartMin,
    config.chartMax,
  )
  const formatter = config.formatar ?? DEFAULT_FORMATTER
  // Para overstriding (usaAbs), mostramos o valor com sinal para o
  // usuário entender se o pé está à frente (+) ou atrás (−) do CoM,
  // mas posicionamos pelo módulo.
  const displayNumero = config.usaAbs
    ? formatter(valorTransformado)
    : formatter(valorTransformado)
  return {
    markerPct,
    idealLeftPct: idealLeft,
    idealWidthPct: Math.max(0, idealRight - idealLeft),
    displayValue: `${displayNumero} ${config.unidade}`,
  }
}

export interface RecomendacaoLike {
  categoria: string
  descricao: string
  severidade: string
}

export function groupBySeveridade<T extends RecomendacaoLike>(
  recomendacoes: readonly T[],
): Record<string, T[]> {
  const grupos: Record<string, T[]> = {
    [SEVERIDADE_CRITICO]: [],
    [SEVERIDADE_ATENCAO]: [],
    [SEVERIDADE_INFORMATIVO]: [],
  }
  for (const rec of recomendacoes) {
    const bucket = grupos[rec.severidade]
    if (bucket) bucket.push(rec)
    else (grupos[rec.severidade] ??= []).push(rec)
  }
  return grupos
}

export interface MetricaLike {
  tipo: string
  valor: number | null
  unidade: string | null
}

export interface MetricaVisual {
  tipo: string
  config: MetricaConfig
  valor: number
  gauge: GaugeGeometry
}

// Constrói lista ordenada de métricas a renderizar como gauges,
// ignorando tipos desconhecidos e valores nulos.
export function buildMetricasVisuais(
  metricas: readonly MetricaLike[],
): MetricaVisual[] {
  const porTipo = new Map<string, MetricaLike>()
  for (const m of metricas) porTipo.set(m.tipo, m)
  const visuais: MetricaVisual[] = []
  for (const tipo of METRIC_DISPLAY_ORDER) {
    const m = porTipo.get(tipo)
    if (!m || m.valor === null || Number.isNaN(m.valor)) continue
    const config = METRIC_CONFIGS[tipo]
    if (!config) continue
    visuais.push({
      tipo,
      config,
      valor: m.valor,
      gauge: buildGaugeGeometry(config, m.valor),
    })
  }
  return visuais
}
