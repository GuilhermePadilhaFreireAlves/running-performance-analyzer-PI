/**
 * MetricIcon — ícones anatômicos inline exibidos nos cards de métrica da
 * tela de diagnóstico (US-039). SVGs geométricos simples (24x24), sem
 * detalhes figurativos; usam `currentColor` para herdar a cor do card.
 * São decorativos — `aria-hidden` é aplicado pelo consumidor.
 */
import type { SVGProps } from 'react'
import type { MetricIconName } from '../../utils/analysisDisplay'

interface MetricIconProps extends SVGProps<SVGSVGElement> {
  name: MetricIconName
  size?: number
}

const STROKE_WIDTH = 1.8

export function MetricIcon({ name, size = 24, ...rest }: MetricIconProps) {
  const common = {
    xmlns: 'http://www.w3.org/2000/svg',
    viewBox: '0 0 24 24',
    width: size,
    height: size,
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth: STROKE_WIDTH,
    strokeLinecap: 'round' as const,
    strokeLinejoin: 'round' as const,
    focusable: false,
    'aria-hidden': true as const,
    ...rest,
  }

  switch (name) {
    case 'joelho':
      return (
        <svg {...common}>
          {/* Perna dobrada no joelho (coxa + canela) */}
          <path d="M6 4 L12 12" />
          <path d="M12 12 L8 20" />
          <circle cx="12" cy="12" r="2.4" />
        </svg>
      )
    case 'cotovelo':
      return (
        <svg {...common}>
          {/* Braço dobrado no cotovelo (úmero + antebraço) */}
          <path d="M4 6 L12 12" />
          <path d="M12 12 L18 6" />
          <circle cx="12" cy="12" r="2.4" />
        </svg>
      )
    case 'tronco':
      return (
        <svg {...common}>
          {/* Tronco inclinado para frente — linha ombro-quadril + seta */}
          <path d="M8 4 L14 18" />
          <path d="M6 20 L18 20" />
          <path d="M14 18 L18 16" />
        </svg>
      )
    case 'passada':
      return (
        <svg {...common}>
          {/* Pegadas (overstriding) — dois pontos no solo */}
          <path d="M4 18 L10 18" />
          <circle cx="7" cy="14" r="2" />
          <path d="M14 8 L20 8" />
          <circle cx="17" cy="12" r="2" />
        </svg>
      )
    case 'oscilacao':
      return (
        <svg {...common}>
          {/* Onda vertical (oscilação do CoM) */}
          <path d="M4 12 C 8 4, 10 20, 14 12 S 20 4, 22 12" />
        </svg>
      )
    case 'simetria':
      return (
        <svg {...common}>
          {/* Espelhamento esq/dir */}
          <path d="M12 4 L12 20" strokeDasharray="2 2" />
          <path d="M4 8 L9 12 L4 16" />
          <path d="M20 8 L15 12 L20 16" />
        </svg>
      )
    case 'cadencia':
      return (
        <svg {...common}>
          {/* Metrônomo — triângulo com pêndulo */}
          <path d="M6 20 L12 4 L18 20 Z" />
          <path d="M12 4 L15 16" />
        </svg>
      )
    case 'tempo':
      return (
        <svg {...common}>
          {/* Cronômetro — círculo com ponteiros */}
          <circle cx="12" cy="13" r="7" />
          <path d="M12 13 L12 9" />
          <path d="M12 13 L15 15" />
          <path d="M10 3 L14 3" />
        </svg>
      )
    default:
      return null
  }
}
