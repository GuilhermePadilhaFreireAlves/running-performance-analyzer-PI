/**
 * LoadingState — placeholder de carregamento que espelha o layout final da
 * página para evitar layout shift (CLS ~0). Cada `variant` renderiza um
 * conjunto de Skeletons com dimensões fixas correspondentes às caixas reais
 * da UI. `aria-busy` + `aria-live="polite"` anunciam o carregamento.
 */
import { Skeleton } from '../Skeleton'

export type LoadingVariant = 'status' | 'analysis' | 'analysis-raw' | 'historico'

export interface LoadingStateProps {
  variant: LoadingVariant
  label?: string
}

export function LoadingState({ variant, label = 'Carregando' }: LoadingStateProps) {
  return (
    <div
      className={`loading-state loading-state-${variant}`}
      role="status"
      aria-busy="true"
      aria-live="polite"
    >
      <span className="visually-hidden">{label}…</span>
      {variant === 'status' ? <StatusSkeleton /> : null}
      {variant === 'analysis' ? <AnalysisSkeleton /> : null}
      {variant === 'analysis-raw' ? <AnalysisRawSkeleton /> : null}
      {variant === 'historico' ? <HistoricoSkeleton /> : null}
    </div>
  )
}

function StatusSkeleton() {
  return (
    <div className="loading-status">
      <Skeleton width="60%" height="20px" />
      <Skeleton width="100%" height="10px" />
      <ul className="loading-status-stages" aria-hidden="true">
        {[0, 1, 2, 3].map((i) => (
          <li key={i} className="loading-status-stage">
            <Skeleton width="14px" height="14px" rounded />
            <Skeleton width="55%" height="14px" />
          </li>
        ))}
      </ul>
      <Skeleton width="45%" height="16px" />
    </div>
  )
}

function AnalysisSkeleton() {
  return (
    <div className="loading-analysis">
      <div className="loading-analysis-hero" aria-hidden="true">
        <Skeleton width="180px" height="180px" rounded />
        <div className="loading-analysis-hero-body">
          <Skeleton width="100px" height="14px" />
          <Skeleton width="180px" height="28px" />
          <Skeleton width="80%" height="16px" />
          <Skeleton width="60%" height="16px" />
        </div>
      </div>
      <div className="loading-analysis-section" aria-hidden="true">
        <Skeleton width="180px" height="22px" />
        <div className="loading-analysis-metric-grid">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="loading-analysis-metric">
              <div className="loading-analysis-metric-header">
                <Skeleton width="36px" height="36px" rounded />
                <Skeleton width="60%" height="14px" />
              </div>
              <Skeleton width="40%" height="22px" />
              <Skeleton width="100%" height="10px" />
            </div>
          ))}
        </div>
      </div>
      <div className="loading-analysis-section" aria-hidden="true">
        <Skeleton width="200px" height="22px" />
        {[0, 1].map((i) => (
          <div key={i} className="loading-analysis-card">
            <Skeleton width="80px" height="18px" />
            <Skeleton width="60%" height="16px" />
            <Skeleton width="95%" height="14px" />
            <Skeleton width="85%" height="14px" />
          </div>
        ))}
      </div>
    </div>
  )
}

function AnalysisRawSkeleton() {
  return (
    <div className="loading-analysis-raw">
      <Skeleton width="55%" height="16px" />
      <div className="loading-raw-grid" aria-hidden="true">
        {[0, 1, 2].map((i) => (
          <div key={i} className="loading-raw-chart">
            <Skeleton width="60%" height="18px" />
            <Skeleton width="100%" height="220px" />
          </div>
        ))}
      </div>
      <div className="loading-raw-asymmetry" aria-hidden="true">
        <Skeleton width="240px" height="22px" />
        {[0, 1].map((i) => (
          <div key={i} className="loading-raw-asymmetry-row">
            <div className="loading-raw-asymmetry-header">
              <Skeleton width="40%" height="14px" />
              <Skeleton width="60px" height="14px" />
            </div>
            <Skeleton width="100%" height="8px" />
          </div>
        ))}
      </div>
    </div>
  )
}

function HistoricoSkeleton() {
  return (
    <div className="loading-historico" aria-hidden="true">
      <div className="loading-historico-hero">
        <div className="loading-historico-hero-stats">
          <Skeleton width="120px" height="14px" />
          <Skeleton width="180px" height="36px" />
          <Skeleton width="200px" height="14px" />
        </div>
        <Skeleton width="220px" height="56px" />
      </div>
      <div className="loading-historico-filters">
        <Skeleton width="80px" height="14px" />
        <Skeleton width="240px" height="32px" />
      </div>
      <ul className="loading-historico-cards">
        {[0, 1, 2, 3, 4].map((i) => (
          <li key={i} className="loading-historico-card">
            <div className="loading-historico-card-row">
              <Skeleton width="55%" height="16px" />
              <Skeleton width="80px" height="22px" />
            </div>
            <div className="loading-historico-card-row">
              <Skeleton width="35%" height="14px" />
              <Skeleton width="60px" height="20px" />
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
