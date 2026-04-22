import { useCallback, useState } from 'react'
import type { ChangeEvent } from 'react'
import {
  PACE_RANGE_MESSAGE,
  formatKmH,
  formatPaceParts,
  isKmHInRange,
  isPaceInRange,
  kmHToPaceParts,
  paceDecimalToKmH,
  paceTextToDecimal,
} from '../utils/pace'

export interface PaceInputValue {
  paceMinKm: number | null
  isValid: boolean
  errorMessage: string | null
}

export interface PaceInputProps {
  onChange?: (value: PaceInputValue) => void
}

const EMPTY_VALUE: PaceInputValue = {
  paceMinKm: null,
  isValid: false,
  errorMessage: null,
}

const INVALID_PACE_FORMAT_MESSAGE =
  'Informe o pace no formato min:ss (ex: 5:30).'
const INVALID_KM_H_MESSAGE = 'Informe a velocidade em km/h (ex: 10.9).'

export function PaceInput({ onChange }: PaceInputProps) {
  const [paceText, setPaceText] = useState('')
  const [kmHText, setKmHText] = useState('')
  const [error, setError] = useState<string | null>(null)

  const emit = useCallback(
    (next: PaceInputValue) => {
      setError(next.errorMessage)
      onChange?.(next)
    },
    [onChange],
  )

  const handlePaceChange = (event: ChangeEvent<HTMLInputElement>) => {
    const text = event.target.value
    setPaceText(text)

    if (text.trim() === '') {
      setKmHText('')
      emit(EMPTY_VALUE)
      return
    }

    const decimal = paceTextToDecimal(text)
    if (decimal === null) {
      setKmHText('')
      emit({
        paceMinKm: null,
        isValid: false,
        errorMessage: INVALID_PACE_FORMAT_MESSAGE,
      })
      return
    }

    const kmH = paceDecimalToKmH(decimal)
    setKmHText(formatKmH(kmH))

    if (!isPaceInRange(decimal)) {
      emit({
        paceMinKm: decimal,
        isValid: false,
        errorMessage: PACE_RANGE_MESSAGE,
      })
      return
    }

    emit({
      paceMinKm: decimal,
      isValid: true,
      errorMessage: null,
    })
  }

  const handleKmHChange = (event: ChangeEvent<HTMLInputElement>) => {
    const text = event.target.value
    setKmHText(text)

    if (text.trim() === '') {
      setPaceText('')
      emit(EMPTY_VALUE)
      return
    }

    const kmH = Number(text)
    if (!Number.isFinite(kmH) || kmH <= 0) {
      setPaceText('')
      emit({
        paceMinKm: null,
        isValid: false,
        errorMessage: INVALID_KM_H_MESSAGE,
      })
      return
    }

    const parts = kmHToPaceParts(kmH)
    setPaceText(formatPaceParts(parts))
    const paceDecimal = parts.min + parts.sec / 60

    if (!isKmHInRange(kmH)) {
      emit({
        paceMinKm: paceDecimal,
        isValid: false,
        errorMessage: PACE_RANGE_MESSAGE,
      })
      return
    }

    emit({
      paceMinKm: paceDecimal,
      isValid: true,
      errorMessage: null,
    })
  }

  return (
    <fieldset className="pace-input">
      <legend>Pace de treino</legend>
      <div className="pace-input-grid">
        <label className="field">
          <span>Pace (min:ss /km)</span>
          <input
            type="text"
            inputMode="numeric"
            placeholder="5:30"
            value={paceText}
            onChange={handlePaceChange}
            aria-invalid={error ? 'true' : 'false'}
            aria-label="Pace em minutos por quilômetro"
          />
        </label>
        <label className="field">
          <span>Velocidade (km/h)</span>
          <input
            type="number"
            inputMode="decimal"
            step="0.1"
            min="0"
            placeholder="10.9"
            value={kmHText}
            onChange={handleKmHChange}
            aria-invalid={error ? 'true' : 'false'}
            aria-label="Velocidade em quilômetros por hora"
          />
        </label>
      </div>
      {error ? (
        <p className="field-error" role="alert">
          {error}
        </p>
      ) : (
        <p className="pace-input-help">
          Faixa aceita: 3:00–12:00 min/km (5–20 km/h).
        </p>
      )}
    </fieldset>
  )
}
