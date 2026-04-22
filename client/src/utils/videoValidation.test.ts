import { describe, it, expect } from 'vitest'
import {
  VIDEO_LOW_FPS_WARNING,
  VIDEO_LOW_QUALITY_MESSAGE,
  VIDEO_TOO_LONG_MESSAGE,
  VIDEO_TOO_SHORT_MESSAGE,
  validateVideoMetadata,
} from './videoValidation'
import type { VideoMetadata } from './videoValidation'

const baseValid: VideoMetadata = {
  durationSec: 60,
  width: 1280,
  height: 720,
  estimatedFps: 60,
}

describe('validateVideoMetadata', () => {
  it('blocks duration shorter than 30 seconds', () => {
    expect(validateVideoMetadata({ ...baseValid, durationSec: 29 })).toEqual({
      isValid: false,
      errorMessage: VIDEO_TOO_SHORT_MESSAGE,
      warnings: [],
    })
  })

  it('blocks duration longer than 3 minutes', () => {
    expect(validateVideoMetadata({ ...baseValid, durationSec: 181 })).toEqual({
      isValid: false,
      errorMessage: VIDEO_TOO_LONG_MESSAGE,
      warnings: [],
    })
  })

  it('blocks width below 640', () => {
    const result = validateVideoMetadata({ ...baseValid, width: 639 })
    expect(result.isValid).toBe(false)
    expect(result.errorMessage).toBe(VIDEO_LOW_QUALITY_MESSAGE)
  })

  it('blocks height below 480', () => {
    const result = validateVideoMetadata({ ...baseValid, height: 479 })
    expect(result.isValid).toBe(false)
    expect(result.errorMessage).toBe(VIDEO_LOW_QUALITY_MESSAGE)
  })

  it('passes valid 60fps video without warnings', () => {
    const result = validateVideoMetadata(baseValid)
    expect(result.isValid).toBe(true)
    expect(result.errorMessage).toBeNull()
    expect(result.warnings).toEqual([])
  })

  it('warns about low FPS but still accepts the video', () => {
    const result = validateVideoMetadata({ ...baseValid, estimatedFps: 30 })
    expect(result.isValid).toBe(true)
    expect(result.errorMessage).toBeNull()
    expect(result.warnings).toContain(VIDEO_LOW_FPS_WARNING)
  })

  it('omits FPS warning when fps cannot be estimated', () => {
    const result = validateVideoMetadata({ ...baseValid, estimatedFps: null })
    expect(result.isValid).toBe(true)
    expect(result.warnings).toEqual([])
  })

  it('treats non-finite duration as too short', () => {
    expect(validateVideoMetadata({ ...baseValid, durationSec: Number.NaN }).isValid).toBe(false)
  })

  it('accepts exactly 30 seconds duration', () => {
    expect(validateVideoMetadata({ ...baseValid, durationSec: 30 }).isValid).toBe(true)
  })

  it('accepts exactly 180 seconds duration', () => {
    expect(validateVideoMetadata({ ...baseValid, durationSec: 180 }).isValid).toBe(true)
  })

  it('accepts exact minimum resolution 640x480', () => {
    const result = validateVideoMetadata({
      ...baseValid,
      width: 640,
      height: 480,
    })
    expect(result.isValid).toBe(true)
  })
})
