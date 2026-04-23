import { describe, expect, it } from 'vitest'
import {
  STATUS_CALCULANDO,
  STATUS_CONCLUIDO,
  STATUS_DETECTANDO_POSE,
  STATUS_ERRO_KEYPOINTS,
  STATUS_ERRO_MULTIPLAS,
  STATUS_PENDENTE,
  STATUS_VALIDANDO,
} from './videoStatus'
import {
  averageNota,
  errorReasonForStatus,
  filterItems,
  FILTRO_STATUS_CONCLUIDO,
  FILTRO_STATUS_ERRO,
  FILTRO_STATUS_TODOS,
  formatCriadoEm,
  formatNotaAverage,
  formatNotaGeral,
  formatPaceMinKm,
  formatTrendDelta,
  isConcluido,
  isProcessing,
  notaTrendDelta,
  parsePageParam,
  parsePeriodoParam,
  parseStatusFilterParam,
  PERIODO_30D,
  PERIODO_7D,
  PERIODO_TODOS,
  sparklinePoints,
  statusBadge,
  totalPages,
  trendDirection,
} from './historicoDisplay'

describe('statusBadge', () => {
  it('maps all processing statuses to "Processando"', () => {
    for (const s of [
      STATUS_PENDENTE,
      STATUS_VALIDANDO,
      STATUS_DETECTANDO_POSE,
      STATUS_CALCULANDO,
    ]) {
      expect(statusBadge(s).label).toBe('Processando')
    }
  })

  it('maps concluido to "Concluído" with done className', () => {
    const badge = statusBadge(STATUS_CONCLUIDO)
    expect(badge.label).toBe('Concluído')
    expect(badge.className).toContain('done')
  })

  it('maps error statuses to "Erro"', () => {
    expect(statusBadge(STATUS_ERRO_KEYPOINTS).label).toBe('Erro')
    expect(statusBadge(STATUS_ERRO_MULTIPLAS).label).toBe('Erro')
  })

  it('falls back to neutral for unknown statuses', () => {
    const badge = statusBadge('desconhecido')
    expect(badge.label).toBe('desconhecido')
    expect(badge.className).toContain('neutral')
  })
})

describe('isConcluido / isProcessing', () => {
  it('classifies concluido', () => {
    expect(isConcluido(STATUS_CONCLUIDO)).toBe(true)
    expect(isConcluido(STATUS_CALCULANDO)).toBe(false)
  })

  it('detects in-progress statuses', () => {
    expect(isProcessing(STATUS_PENDENTE)).toBe(true)
    expect(isProcessing(STATUS_VALIDANDO)).toBe(true)
    expect(isProcessing(STATUS_DETECTANDO_POSE)).toBe(true)
    expect(isProcessing(STATUS_CALCULANDO)).toBe(true)
    expect(isProcessing(STATUS_CONCLUIDO)).toBe(false)
    expect(isProcessing(STATUS_ERRO_KEYPOINTS)).toBe(false)
  })
})

describe('errorReasonForStatus', () => {
  it('returns PRD message for error statuses', () => {
    expect(errorReasonForStatus(STATUS_ERRO_KEYPOINTS)).not.toBeNull()
    expect(errorReasonForStatus(STATUS_ERRO_MULTIPLAS)).not.toBeNull()
  })

  it('returns null for non-error statuses', () => {
    expect(errorReasonForStatus(STATUS_CONCLUIDO)).toBeNull()
    expect(errorReasonForStatus(STATUS_CALCULANDO)).toBeNull()
  })
})

describe('formatPaceMinKm', () => {
  it('formats pace decimals with zero-padded seconds', () => {
    expect(formatPaceMinKm(5.5)).toBe('5:30 /km')
    expect(formatPaceMinKm(4)).toBe('4:00 /km')
    expect(formatPaceMinKm(5.25)).toBe('5:15 /km')
  })

  it('returns em-dash for null, NaN, or non-positive values', () => {
    expect(formatPaceMinKm(null)).toBe('—')
    expect(formatPaceMinKm(Number.NaN)).toBe('—')
    expect(formatPaceMinKm(0)).toBe('—')
    expect(formatPaceMinKm(-5)).toBe('—')
  })
})

describe('formatNotaGeral', () => {
  it('formats nota with 1 decimal and /10 suffix', () => {
    expect(formatNotaGeral(7.25)).toBe('7.3/10')
    expect(formatNotaGeral(10)).toBe('10.0/10')
    expect(formatNotaGeral(0)).toBe('0.0/10')
  })

  it('returns em-dash for null or NaN', () => {
    expect(formatNotaGeral(null)).toBe('—')
    expect(formatNotaGeral(Number.NaN)).toBe('—')
  })
})

describe('formatCriadoEm', () => {
  it('formats ISO datetime as dd/mm/yyyy HH:MM', () => {
    // Use a timezone-aware ISO string — Date parses to local TZ.
    // Build a local Date so the test is deterministic regardless of host TZ.
    const d = new Date(2026, 3, 21, 14, 5)
    const formatted = formatCriadoEm(d.toISOString())
    expect(formatted).toMatch(/^\d{2}\/\d{2}\/\d{4} \d{2}:\d{2}$/)
  })

  it('returns raw string when parse fails', () => {
    expect(formatCriadoEm('not a date')).toBe('not a date')
  })
})

describe('parsePageParam', () => {
  it('defaults to 1 for null or invalid values', () => {
    expect(parsePageParam(null)).toBe(1)
    expect(parsePageParam('')).toBe(1)
    expect(parsePageParam('0')).toBe(1)
    expect(parsePageParam('-3')).toBe(1)
    expect(parsePageParam('abc')).toBe(1)
  })

  it('parses positive integers', () => {
    expect(parsePageParam('1')).toBe(1)
    expect(parsePageParam('5')).toBe(5)
    expect(parsePageParam('42')).toBe(42)
  })
})

describe('totalPages', () => {
  it('returns at least 1', () => {
    expect(totalPages(0, 10)).toBe(1)
    expect(totalPages(-5, 10)).toBe(1)
  })

  it('rounds up partial pages', () => {
    expect(totalPages(10, 10)).toBe(1)
    expect(totalPages(11, 10)).toBe(2)
    expect(totalPages(21, 10)).toBe(3)
    expect(totalPages(60, 10)).toBe(6)
  })

  it('handles zero limit defensively', () => {
    expect(totalPages(10, 0)).toBe(1)
  })
})

describe('parsePeriodoParam', () => {
  it('accepts known periods', () => {
    expect(parsePeriodoParam('7d')).toBe(PERIODO_7D)
    expect(parsePeriodoParam('30d')).toBe(PERIODO_30D)
    expect(parsePeriodoParam('todos')).toBe(PERIODO_TODOS)
  })

  it('falls back to "todos" for null or unknown values', () => {
    expect(parsePeriodoParam(null)).toBe(PERIODO_TODOS)
    expect(parsePeriodoParam('')).toBe(PERIODO_TODOS)
    expect(parsePeriodoParam('ontem')).toBe(PERIODO_TODOS)
  })
})

describe('parseStatusFilterParam', () => {
  it('accepts known filters', () => {
    expect(parseStatusFilterParam('concluido')).toBe(FILTRO_STATUS_CONCLUIDO)
    expect(parseStatusFilterParam('erro')).toBe(FILTRO_STATUS_ERRO)
  })

  it('falls back to "todos" for anything else', () => {
    expect(parseStatusFilterParam(null)).toBe(FILTRO_STATUS_TODOS)
    expect(parseStatusFilterParam('xyz')).toBe(FILTRO_STATUS_TODOS)
  })
})

describe('filterItems', () => {
  const now = new Date('2026-04-22T12:00:00.000Z')
  const items = [
    {
      id: 1,
      criado_em: '2026-04-22T10:00:00.000Z',
      status: STATUS_CONCLUIDO,
      nota_geral: 8.5,
    },
    {
      id: 2,
      criado_em: '2026-04-17T09:00:00.000Z',
      status: STATUS_CONCLUIDO,
      nota_geral: 7.2,
    },
    {
      id: 3,
      criado_em: '2026-04-01T09:00:00.000Z',
      status: STATUS_ERRO_KEYPOINTS,
      nota_geral: null,
    },
    {
      id: 4,
      criado_em: '2026-02-01T09:00:00.000Z',
      status: STATUS_CONCLUIDO,
      nota_geral: 6.1,
    },
  ]

  it('keeps only items within the last 7 days', () => {
    const result = filterItems(items, PERIODO_7D, FILTRO_STATUS_TODOS, now)
    expect(result.map((i) => i.id)).toEqual([1, 2])
  })

  it('keeps only items within the last 30 days', () => {
    const result = filterItems(items, PERIODO_30D, FILTRO_STATUS_TODOS, now)
    expect(result.map((i) => i.id)).toEqual([1, 2, 3])
  })

  it('returns everything when periodo is "todos" and filter is "todos"', () => {
    const result = filterItems(items, PERIODO_TODOS, FILTRO_STATUS_TODOS, now)
    expect(result.map((i) => i.id)).toEqual([1, 2, 3, 4])
  })

  it('combines periodo + status filter', () => {
    const result = filterItems(items, PERIODO_30D, FILTRO_STATUS_CONCLUIDO, now)
    expect(result.map((i) => i.id)).toEqual([1, 2])
  })

  it('keeps error items when status=erro', () => {
    const result = filterItems(items, PERIODO_TODOS, FILTRO_STATUS_ERRO, now)
    expect(result.map((i) => i.id)).toEqual([3])
  })
})

describe('sparklinePoints', () => {
  it('keeps only concluidos with a nota and orders chronologically ascending', () => {
    const pts = sparklinePoints([
      { criado_em: '2026-04-22T10:00:00.000Z', status: STATUS_CONCLUIDO, nota_geral: 8 },
      { criado_em: '2026-04-20T10:00:00.000Z', status: STATUS_CONCLUIDO, nota_geral: 7 },
      { criado_em: '2026-04-21T10:00:00.000Z', status: STATUS_ERRO_KEYPOINTS, nota_geral: null },
      { criado_em: '2026-04-19T10:00:00.000Z', status: STATUS_CONCLUIDO, nota_geral: null },
    ])
    expect(pts.map((p) => p.nota)).toEqual([7, 8])
    expect(pts[0].idx).toBe(0)
    expect(pts[1].idx).toBe(1)
  })
})

describe('averageNota / notaTrendDelta', () => {
  const items = [
    { criado_em: '2026-04-22T10:00:00.000Z', status: STATUS_CONCLUIDO, nota_geral: 8 },
    { criado_em: '2026-04-20T10:00:00.000Z', status: STATUS_CONCLUIDO, nota_geral: 6 },
    { criado_em: '2026-04-15T10:00:00.000Z', status: STATUS_CONCLUIDO, nota_geral: 5 },
    { criado_em: '2026-04-10T10:00:00.000Z', status: STATUS_CONCLUIDO, nota_geral: 4 },
  ]

  it('averageNota ignores non-concluidos and nulls', () => {
    expect(averageNota(items)).toBeCloseTo(5.75)
    expect(
      averageNota([
        { criado_em: '2026-01-01T00:00:00.000Z', status: STATUS_ERRO_KEYPOINTS, nota_geral: null },
      ]),
    ).toBeNull()
  })

  it('notaTrendDelta compares newer half vs older half', () => {
    // older: 4, 5 → avg 4.5; newer: 6, 8 → avg 7 ⇒ delta +2.5
    expect(notaTrendDelta(items)).toBeCloseTo(2.5)
  })

  it('returns null when less than 2 concluidos', () => {
    expect(
      notaTrendDelta([
        { criado_em: '2026-04-22T10:00:00.000Z', status: STATUS_CONCLUIDO, nota_geral: 8 },
      ]),
    ).toBeNull()
  })
})

describe('formatNotaAverage / formatTrendDelta / trendDirection', () => {
  it('formats average with one decimal', () => {
    expect(formatNotaAverage(7.24)).toBe('7.2')
    expect(formatNotaAverage(null)).toBe('—')
  })

  it('formats trend with sign prefix', () => {
    expect(formatTrendDelta(0.8)).toBe('+0.8')
    expect(formatTrendDelta(-1.2)).toBe('−1.2')
    expect(formatTrendDelta(0)).toBe('±0.0')
    expect(formatTrendDelta(null)).toBe('')
  })

  it('classifies trend direction with epsilon', () => {
    expect(trendDirection(0.5)).toBe('up')
    expect(trendDirection(-0.5)).toBe('down')
    expect(trendDirection(0.01)).toBe('flat')
    expect(trendDirection(null)).toBeNull()
  })
})
