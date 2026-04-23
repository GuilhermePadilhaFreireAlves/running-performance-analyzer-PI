/**
 * RunnerHero — ilustração SVG com motion lines que pulsam ao ritmo da
 * etapa ativa. O `stage` controla a velocidade via custom property CSS
 * (`--runner-speed`) aplicada ao wrapper, e `isCelebrating` alterna para
 * um pulso mais calmo/celebratório quando a análise termina. A animação
 * é desativada automaticamente via `prefers-reduced-motion` pelo global
 * em index.css.
 */

export interface RunnerHeroProps {
  stage: number
  isCelebrating?: boolean
}

const STAGE_SPEED: Record<number, string> = {
  0: '1.6s',
  1: '1.3s',
  2: '1.0s',
  3: '0.8s',
}

export function RunnerHero({ stage, isCelebrating = false }: RunnerHeroProps) {
  const speed = STAGE_SPEED[stage] ?? '1.2s'
  const className = [
    'status-hero-runner',
    isCelebrating ? 'status-hero-runner-celebrating' : '',
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <div
      className={className}
      style={{ ['--runner-speed' as string]: speed }}
      aria-hidden="true"
    >
      <svg viewBox="0 0 220 120" role="presentation" focusable="false">
        <g className="runner-motion-lines">
          <line x1="8" y1="42" x2="38" y2="42" className="runner-motion-line runner-motion-line-1" />
          <line x1="8" y1="62" x2="46" y2="62" className="runner-motion-line runner-motion-line-2" />
          <line x1="8" y1="82" x2="32" y2="82" className="runner-motion-line runner-motion-line-3" />
        </g>
        <g className="runner-figure">
          <circle cx="150" cy="30" r="10" className="runner-head" />
          <path
            d="M150 40 L146 75"
            className="runner-torso"
            strokeLinecap="round"
          />
          <path
            d="M148 50 L166 62"
            className="runner-arm runner-arm-front"
            strokeLinecap="round"
          />
          <path
            d="M148 50 L132 62"
            className="runner-arm runner-arm-back"
            strokeLinecap="round"
          />
          <path
            d="M146 75 L168 95"
            className="runner-leg runner-leg-front"
            strokeLinecap="round"
          />
          <path
            d="M146 75 L126 95"
            className="runner-leg runner-leg-back"
            strokeLinecap="round"
          />
        </g>
        <line
          x1="10"
          y1="110"
          x2="210"
          y2="110"
          className="runner-ground"
          strokeLinecap="round"
        />
      </svg>
    </div>
  )
}
