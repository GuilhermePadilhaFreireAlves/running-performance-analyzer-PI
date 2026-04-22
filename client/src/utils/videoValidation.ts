export const VIDEO_MIN_DURATION_SEC = 30
export const VIDEO_MAX_DURATION_SEC = 180
export const VIDEO_MIN_WIDTH = 640
export const VIDEO_MIN_HEIGHT = 480
export const VIDEO_MIN_FPS = 60

export const VIDEO_TOO_SHORT_MESSAGE =
  'Vídeo muito curto — grave pelo menos 30 segundos de corrida contínua'
export const VIDEO_TOO_LONG_MESSAGE =
  'Vídeo muito longo — envie no máximo 3 minutos'
export const VIDEO_LOW_QUALITY_MESSAGE =
  'Qualidade insuficiente — grave em no mínimo 480p'
export const VIDEO_LOW_FPS_WARNING =
  'FPS estimado abaixo de 60. O backend fará a validação definitiva — o envio pode ser recusado se o vídeo não tiver pelo menos 60 FPS.'

export interface VideoMetadata {
  durationSec: number
  width: number
  height: number
  estimatedFps: number | null
}

export interface VideoValidationResult {
  isValid: boolean
  errorMessage: string | null
  warnings: string[]
}

export function validateVideoMetadata(
  meta: VideoMetadata,
): VideoValidationResult {
  if (!Number.isFinite(meta.durationSec) || meta.durationSec <= 0) {
    return {
      isValid: false,
      errorMessage: VIDEO_TOO_SHORT_MESSAGE,
      warnings: [],
    }
  }
  if (meta.durationSec < VIDEO_MIN_DURATION_SEC) {
    return {
      isValid: false,
      errorMessage: VIDEO_TOO_SHORT_MESSAGE,
      warnings: [],
    }
  }
  if (meta.durationSec > VIDEO_MAX_DURATION_SEC) {
    return {
      isValid: false,
      errorMessage: VIDEO_TOO_LONG_MESSAGE,
      warnings: [],
    }
  }
  if (meta.width < VIDEO_MIN_WIDTH || meta.height < VIDEO_MIN_HEIGHT) {
    return {
      isValid: false,
      errorMessage: VIDEO_LOW_QUALITY_MESSAGE,
      warnings: [],
    }
  }
  const warnings: string[] = []
  if (meta.estimatedFps !== null && meta.estimatedFps < VIDEO_MIN_FPS) {
    warnings.push(VIDEO_LOW_FPS_WARNING)
  }
  return {
    isValid: true,
    errorMessage: null,
    warnings,
  }
}
