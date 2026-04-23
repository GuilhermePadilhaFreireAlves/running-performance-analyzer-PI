import type { SVGProps } from 'react'

interface LogoProps extends SVGProps<SVGSVGElement> {
  /** Tamanho em pixels (largura e altura). Default 28. */
  size?: number
  /** Título acessível. Quando ausente, role=img + aria-hidden. */
  title?: string
}

/**
 * Símbolo abstrato de movimento — três barras inclinadas que evocam passos
 * em progressão. Geométrico simples; consome `currentColor` para herdar a cor
 * do contexto (top nav, footer, favicon).
 */
export function Logo({ size = 28, title, ...rest }: LogoProps) {
  const accessibleProps = title
    ? { role: 'img' as const, 'aria-label': title }
    : { 'aria-hidden': true as const, focusable: false as const }
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 32 32"
      width={size}
      height={size}
      fill="none"
      {...accessibleProps}
      {...rest}
    >
      {title ? <title>{title}</title> : null}
      <path
        d="M6 22 L12 10"
        stroke="currentColor"
        strokeWidth="3.2"
        strokeLinecap="round"
      />
      <path
        d="M14 24 L20 10"
        stroke="currentColor"
        strokeWidth="3.2"
        strokeLinecap="round"
        opacity="0.75"
      />
      <path
        d="M22 26 L28 12"
        stroke="currentColor"
        strokeWidth="3.2"
        strokeLinecap="round"
        opacity="0.45"
      />
    </svg>
  )
}
