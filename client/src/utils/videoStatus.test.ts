import { describe, expect, it } from 'vitest'
import {
  ERROR_KEYPOINTS_MESSAGE,
  ERROR_MULTIPLAS_PESSOAS_MESSAGE,
  STATUS_CALCULANDO,
  STATUS_CONCLUIDO,
  STATUS_DETECTANDO_POSE,
  STATUS_ERRO_KEYPOINTS,
  STATUS_ERRO_MULTIPLAS,
  STATUS_PENDENTE,
  STATUS_VALIDANDO,
  errorMessageForStatus,
  estimatedRemainingLabel,
  formatElapsedTime,
  isErrorStatus,
  isFinalStatus,
  progressPercentFromStatus,
  stageIndexFromStatus,
} from './videoStatus'

describe('stageIndexFromStatus', () => {
  it('maps pendente and validando to stage 0', () => {
    expect(stageIndexFromStatus(STATUS_PENDENTE)).toBe(0)
    expect(stageIndexFromStatus(STATUS_VALIDANDO)).toBe(0)
  })

  it('maps detectando_pose to stage 1', () => {
    expect(stageIndexFromStatus(STATUS_DETECTANDO_POSE)).toBe(1)
  })

  it('maps calculando_metricas to stage 2', () => {
    expect(stageIndexFromStatus(STATUS_CALCULANDO)).toBe(2)
  })

  it('maps concluido to stage 3', () => {
    expect(stageIndexFromStatus(STATUS_CONCLUIDO)).toBe(3)
  })

  it('falls back to 0 for unknown status', () => {
    expect(stageIndexFromStatus('qualquer_coisa')).toBe(0)
  })
})

describe('progressPercentFromStatus', () => {
  it('returns 100 for concluido', () => {
    expect(progressPercentFromStatus(STATUS_CONCLUIDO)).toBe(100)
  })

  it('returns increasing percentages for earlier stages', () => {
    const a = progressPercentFromStatus(STATUS_VALIDANDO)
    const b = progressPercentFromStatus(STATUS_DETECTANDO_POSE)
    const c = progressPercentFromStatus(STATUS_CALCULANDO)
    expect(a).toBeLessThan(b)
    expect(b).toBeLessThan(c)
    expect(c).toBeLessThan(100)
    expect(a).toBeGreaterThan(0)
  })
})

describe('isErrorStatus / errorMessageForStatus', () => {
  it('detects both error statuses', () => {
    expect(isErrorStatus(STATUS_ERRO_KEYPOINTS)).toBe(true)
    expect(isErrorStatus(STATUS_ERRO_MULTIPLAS)).toBe(true)
    expect(isErrorStatus(STATUS_CONCLUIDO)).toBe(false)
  })

  it('returns PRD-aligned messages for each error', () => {
    expect(errorMessageForStatus(STATUS_ERRO_KEYPOINTS)).toBe(
      ERROR_KEYPOINTS_MESSAGE,
    )
    expect(errorMessageForStatus(STATUS_ERRO_MULTIPLAS)).toBe(
      ERROR_MULTIPLAS_PESSOAS_MESSAGE,
    )
    expect(errorMessageForStatus(STATUS_CONCLUIDO)).toBeNull()
  })
})

describe('isFinalStatus', () => {
  it('treats concluido and errors as final', () => {
    expect(isFinalStatus(STATUS_CONCLUIDO)).toBe(true)
    expect(isFinalStatus(STATUS_ERRO_KEYPOINTS)).toBe(true)
    expect(isFinalStatus(STATUS_ERRO_MULTIPLAS)).toBe(true)
  })

  it('treats in-progress statuses as non-final', () => {
    expect(isFinalStatus(STATUS_PENDENTE)).toBe(false)
    expect(isFinalStatus(STATUS_VALIDANDO)).toBe(false)
    expect(isFinalStatus(STATUS_DETECTANDO_POSE)).toBe(false)
    expect(isFinalStatus(STATUS_CALCULANDO)).toBe(false)
  })
})

describe('formatElapsedTime', () => {
  it('formats sub-minute elapsed as "Há N segundos"', () => {
    expect(formatElapsedTime(0)).toBe('Há 1 segundo')
    expect(formatElapsedTime(1)).toBe('Há 1 segundo')
    expect(formatElapsedTime(12)).toBe('Há 12 segundos')
    expect(formatElapsedTime(59)).toBe('Há 59 segundos')
  })

  it('formats whole minutes as "Há N minutos"', () => {
    expect(formatElapsedTime(60)).toBe('Há 1 minuto')
    expect(formatElapsedTime(120)).toBe('Há 2 minutos')
  })

  it('combines minutes + seconds when both are non-zero', () => {
    expect(formatElapsedTime(90)).toBe('Há 1 minuto e 30 segundos')
    expect(formatElapsedTime(125)).toBe('Há 2 minutos e 5 segundos')
    expect(formatElapsedTime(61)).toBe('Há 1 minuto e 1 segundo')
  })

  it('clamps negatives to zero', () => {
    expect(formatElapsedTime(-5)).toBe('Há 1 segundo')
  })
})

describe('estimatedRemainingLabel', () => {
  it('decreases with elapsed time', () => {
    const early = estimatedRemainingLabel(0)
    const mid = estimatedRemainingLabel(15)
    expect(early).toBe('~35s restantes')
    expect(mid).toBe('~20s restantes')
  })

  it('never drops below 5 seconds', () => {
    expect(estimatedRemainingLabel(60)).toBe('~5s restantes')
    expect(estimatedRemainingLabel(999)).toBe('~5s restantes')
  })
})
