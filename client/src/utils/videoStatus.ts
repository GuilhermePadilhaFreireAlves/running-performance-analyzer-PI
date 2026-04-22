export const STATUS_PENDENTE = 'pendente'
export const STATUS_VALIDANDO = 'validando_perspectiva'
export const STATUS_DETECTANDO_POSE = 'detectando_pose'
export const STATUS_CALCULANDO = 'calculando_metricas'
export const STATUS_CONCLUIDO = 'concluido'
export const STATUS_ERRO_KEYPOINTS = 'erro_qualidade_keypoints'
export const STATUS_ERRO_MULTIPLAS = 'erro_multiplas_pessoas'

export const ERROR_KEYPOINTS_MESSAGE =
  'Não foi possível analisar este vídeo: qualidade de keypoints insuficiente. Grave com boa iluminação, com o corpo todo visível e sem obstruções.'
export const ERROR_MULTIPLAS_PESSOAS_MESSAGE =
  'Não foi possível analisar este vídeo: múltiplas pessoas foram detectadas. Grave um vídeo com apenas o corredor em cena.'

export interface StatusStage {
  key: string
  label: string
}

export const STATUS_STAGES: readonly StatusStage[] = [
  { key: STATUS_VALIDANDO, label: 'Validando perspectiva' },
  { key: STATUS_DETECTANDO_POSE, label: 'Detectando pose com YOLOv8' },
  { key: STATUS_CALCULANDO, label: 'Calculando métricas' },
  { key: STATUS_CONCLUIDO, label: 'Concluído' },
] as const

const STAGE_INDEX_BY_STATUS: Record<string, number> = {
  [STATUS_PENDENTE]: 0,
  [STATUS_VALIDANDO]: 0,
  [STATUS_DETECTANDO_POSE]: 1,
  [STATUS_CALCULANDO]: 2,
  [STATUS_CONCLUIDO]: 3,
}

export function stageIndexFromStatus(status: string): number {
  const idx = STAGE_INDEX_BY_STATUS[status]
  return idx === undefined ? 0 : idx
}

export function progressPercentFromStatus(status: string): number {
  if (status === STATUS_CONCLUIDO) return 100
  const idx = stageIndexFromStatus(status)
  const total = STATUS_STAGES.length
  return Math.round(((idx + 1) / total) * 100 - 100 / (total * 2))
}

export function isErrorStatus(status: string): boolean {
  return (
    status === STATUS_ERRO_KEYPOINTS || status === STATUS_ERRO_MULTIPLAS
  )
}

export function errorMessageForStatus(status: string): string | null {
  if (status === STATUS_ERRO_KEYPOINTS) return ERROR_KEYPOINTS_MESSAGE
  if (status === STATUS_ERRO_MULTIPLAS) return ERROR_MULTIPLAS_PESSOAS_MESSAGE
  return null
}

export function isFinalStatus(status: string): boolean {
  return status === STATUS_CONCLUIDO || isErrorStatus(status)
}
