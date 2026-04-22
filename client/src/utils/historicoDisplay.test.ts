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
  errorReasonForStatus,
  formatCriadoEm,
  formatNotaGeral,
  formatPaceMinKm,
  isConcluido,
  isProcessing,
  parsePageParam,
  statusBadge,
  totalPages,
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
