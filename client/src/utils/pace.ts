export const PACE_MIN_KM_MIN = 3.0
export const PACE_MIN_KM_MAX = 12.0
export const KM_H_MIN = 5.0
export const KM_H_MAX = 20.0

export const PACE_RANGE_MESSAGE =
  'Pace fora da faixa aceita (3:00–12:00 min/km, equivalente a 5–20 km/h).'

export interface PaceParts {
  min: number
  sec: number
}

export function paceTextToDecimal(text: string): number | null {
  const trimmed = text.trim()
  if (!trimmed) return null

  if (trimmed.includes(':')) {
    const parts = trimmed.split(':')
    if (parts.length !== 2) return null
    const minStr = parts[0].trim()
    const secStr = parts[1].trim()
    if (!minStr || !secStr) return null
    const min = Number(minStr)
    const sec = Number(secStr)
    if (!Number.isFinite(min) || !Number.isFinite(sec)) return null
    if (!Number.isInteger(min) || min < 0) return null
    if (sec < 0 || sec >= 60) return null
    return min + sec / 60
  }

  const value = Number(trimmed)
  if (!Number.isFinite(value) || value < 0) return null
  return value
}

export function paceDecimalToKmH(paceDecimal: number): number {
  if (paceDecimal <= 0) return Number.POSITIVE_INFINITY
  return 60 / paceDecimal
}

export function kmHToPaceParts(kmH: number): PaceParts {
  if (kmH <= 0) return { min: 0, sec: 0 }
  const paceDecimal = 60 / kmH
  const min = Math.floor(paceDecimal)
  const sec = Math.round((paceDecimal % 1) * 60)
  if (sec === 60) {
    return { min: min + 1, sec: 0 }
  }
  return { min, sec }
}

export function paceDecimalFromParts({ min, sec }: PaceParts): number {
  return min + sec / 60
}

export function formatPaceParts({ min, sec }: PaceParts): string {
  const sec2 = sec.toString().padStart(2, '0')
  return `${min}:${sec2}`
}

export function formatKmH(kmH: number): string {
  if (!Number.isFinite(kmH)) return ''
  return kmH.toFixed(1)
}

export function isPaceInRange(paceDecimal: number): boolean {
  return paceDecimal >= PACE_MIN_KM_MIN && paceDecimal <= PACE_MIN_KM_MAX
}

export function isKmHInRange(kmH: number): boolean {
  return kmH >= KM_H_MIN && kmH <= KM_H_MAX
}
