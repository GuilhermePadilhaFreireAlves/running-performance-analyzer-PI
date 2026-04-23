/**
 * Skeleton — placeholder pulsante para estados de loading. `width` e
 * `height` aceitam qualquer valor CSS (ex: `'12ch'`, `'40px'`, `'100%'`)
 * para espelhar o layout final e prevenir layout shift (CLS) ao trocar
 * skeleton pelo conteúdo real. `rounded=true` aplica `radius-full`
 * (use para avatares/círculos).
 */
import type { CSSProperties } from 'react'

export interface SkeletonProps {
  width?: string
  height?: string
  rounded?: boolean
  className?: string
  'aria-label'?: string
}

export function Skeleton({
  width,
  height,
  rounded = false,
  className,
  'aria-label': ariaLabel = 'Carregando',
}: SkeletonProps) {
  const classes = [
    'ui-skeleton',
    rounded ? 'ui-skeleton-rounded' : '',
    className ?? '',
  ]
    .filter(Boolean)
    .join(' ')

  const style: CSSProperties = {}
  if (width !== undefined) style.width = width
  if (height !== undefined) style.height = height

  return (
    <span
      className={classes}
      style={style}
      role="status"
      aria-label={ariaLabel}
    />
  )
}
