import { describe, expect, it } from 'vitest'
import {
  formatKmH,
  formatPaceParts,
  isKmHInRange,
  isPaceInRange,
  kmHToPaceParts,
  paceDecimalFromParts,
  paceDecimalToKmH,
  paceTextToDecimal,
} from './pace'

describe('paceTextToDecimal', () => {
  it('parses min:ss into decimal minutes', () => {
    expect(paceTextToDecimal('5:30')).toBe(5.5)
    expect(paceTextToDecimal('3:45')).toBe(3.75)
    expect(paceTextToDecimal('12:00')).toBe(12)
    expect(paceTextToDecimal('5:05')).toBeCloseTo(5 + 5 / 60, 10)
  })

  it('parses bare integer minutes', () => {
    expect(paceTextToDecimal('5')).toBe(5)
    expect(paceTextToDecimal('  6  ')).toBe(6)
  })

  it('returns null for invalid input', () => {
    expect(paceTextToDecimal('')).toBeNull()
    expect(paceTextToDecimal('abc')).toBeNull()
    expect(paceTextToDecimal('5:60')).toBeNull()
    expect(paceTextToDecimal('5:-1')).toBeNull()
    expect(paceTextToDecimal('-1:00')).toBeNull()
    expect(paceTextToDecimal('5:30:00')).toBeNull()
    expect(paceTextToDecimal(':30')).toBeNull()
    expect(paceTextToDecimal('5:')).toBeNull()
  })
})

describe('paceDecimalToKmH', () => {
  it('applies km_h = 60 / pace_decimal', () => {
    expect(paceDecimalToKmH(5.5)).toBeCloseTo(10.909, 3)
    expect(paceDecimalToKmH(3)).toBe(20)
    expect(paceDecimalToKmH(12)).toBe(5)
    expect(paceDecimalToKmH(6)).toBe(10)
  })
})

describe('kmHToPaceParts', () => {
  it('applies pace_min = floor(60 / km_h) and pace_seg = round((60/km_h % 1) × 60)', () => {
    expect(kmHToPaceParts(10.9)).toEqual({ min: 5, sec: 30 })
    expect(kmHToPaceParts(20)).toEqual({ min: 3, sec: 0 })
    expect(kmHToPaceParts(5)).toEqual({ min: 12, sec: 0 })
    expect(kmHToPaceParts(10)).toEqual({ min: 6, sec: 0 })
  })

  it('carries 60 seconds into the next minute', () => {
    // 60 / km_h × 60 → 59.5 seconds rounds to 60; should bump to next minute
    // pick a km/h so seconds round to 60
    const kmH = 60 / (5 + 59.6 / 60) // pace ~5:59.6
    expect(kmHToPaceParts(kmH)).toEqual({ min: 6, sec: 0 })
  })
})

describe('formatPaceParts', () => {
  it('zero-pads seconds', () => {
    expect(formatPaceParts({ min: 5, sec: 30 })).toBe('5:30')
    expect(formatPaceParts({ min: 5, sec: 5 })).toBe('5:05')
    expect(formatPaceParts({ min: 12, sec: 0 })).toBe('12:00')
  })
})

describe('formatKmH', () => {
  it('rounds to 1 decimal place', () => {
    expect(formatKmH(10.909)).toBe('10.9')
    expect(formatKmH(20)).toBe('20.0')
    expect(formatKmH(5)).toBe('5.0')
  })
})

describe('paceDecimalFromParts', () => {
  it('combines min and sec into decimal', () => {
    expect(paceDecimalFromParts({ min: 5, sec: 30 })).toBe(5.5)
    expect(paceDecimalFromParts({ min: 3, sec: 45 })).toBe(3.75)
  })
})

describe('roundtrip 5:30 ↔ 10.9 km/h', () => {
  it('5:30/km converts to 10.9 km/h (rounded display)', () => {
    const decimal = paceTextToDecimal('5:30')
    expect(decimal).not.toBeNull()
    const kmH = paceDecimalToKmH(decimal as number)
    expect(formatKmH(kmH)).toBe('10.9')
  })

  it('10.9 km/h converts back to 5:30 /km', () => {
    const parts = kmHToPaceParts(10.9)
    expect(formatPaceParts(parts)).toBe('5:30')
  })
})

describe('range guards', () => {
  it('isPaceInRange covers [3, 12] inclusive', () => {
    expect(isPaceInRange(2.99)).toBe(false)
    expect(isPaceInRange(3)).toBe(true)
    expect(isPaceInRange(5.5)).toBe(true)
    expect(isPaceInRange(12)).toBe(true)
    expect(isPaceInRange(12.01)).toBe(false)
  })

  it('isKmHInRange covers [5, 20] inclusive', () => {
    expect(isKmHInRange(4.99)).toBe(false)
    expect(isKmHInRange(5)).toBe(true)
    expect(isKmHInRange(10.9)).toBe(true)
    expect(isKmHInRange(20)).toBe(true)
    expect(isKmHInRange(20.01)).toBe(false)
  })
})
