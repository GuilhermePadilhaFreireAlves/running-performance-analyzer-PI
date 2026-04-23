/**
 * Card — container de conteúdo com surface, raio-lg e shadow-sm. `title`
 * é opcional; `as` escolhe a tag semântica do título (h1..h6, default h2).
 */
import type { ReactNode } from 'react'

export type CardTitleTag = 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6'

export interface CardProps {
  title?: ReactNode
  as?: CardTitleTag
  className?: string
  children?: ReactNode
}

export function Card({
  title,
  as: Tag = 'h2',
  className,
  children,
}: CardProps) {
  const classes = ['ui-card', className ?? ''].filter(Boolean).join(' ')

  return (
    <section className={classes}>
      {title !== undefined && title !== null && title !== '' ? (
        <Tag className="ui-card-title">{title}</Tag>
      ) : null}
      {children !== undefined ? (
        <div className="ui-card-body">{children}</div>
      ) : null}
    </section>
  )
}
