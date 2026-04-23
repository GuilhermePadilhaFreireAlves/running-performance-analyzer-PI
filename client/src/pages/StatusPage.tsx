import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { getVideoStatusRequest } from '../api/videos'
import type { VideoStatusResponse } from '../api/videos'
import { extractApiError } from '../api/errors'
import {
  STATUS_STAGES,
  errorMessageForStatus,
  estimatedRemainingLabel,
  formatElapsedTime,
  isErrorStatus,
  isFinalStatus,
  progressPercentFromStatus,
  stageIndexFromStatus,
  STATUS_CONCLUIDO,
} from '../utils/videoStatus'
import { usePageTitle } from '../hooks/usePageTitle'
import { useToast } from '../context/ToastContext'
import { Banner, Button, ErrorState, LoadingState } from '../components/ui'
import { RunnerHero } from '../components/RunnerHero'

const POLL_INTERVAL_MS = 2000
const CELEBRATION_REDIRECT_MS = 1500
const CELEBRATION_STAGE_INDEX = STATUS_STAGES.length

interface FetchState {
  status: VideoStatusResponse | null
  error: string | null
  loading: boolean
}

const INITIAL_STATE: FetchState = {
  status: null,
  error: null,
  loading: true,
}

export default function StatusPage() {
  usePageTitle('Processando')
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const toast = useToast()
  const [state, setState] = useState<FetchState>(INITIAL_STATE)
  const [elapsedSeconds, setElapsedSeconds] = useState(0)
  const timerRef = useRef<number | null>(null)
  const cancelledRef = useRef(false)
  const errorNotifiedRef = useRef<string | null>(null)
  const startedAtRef = useRef<number>(Date.now())

  useEffect(() => {
    if (!id) return
    cancelledRef.current = false
    startedAtRef.current = Date.now()

    const poll = async () => {
      try {
        const data = await getVideoStatusRequest(id)
        if (cancelledRef.current) return
        errorNotifiedRef.current = null
        setState({ status: data, error: null, loading: false })
        if (isFinalStatus(data.status)) {
          cancelledRef.current = true
          return
        }
        timerRef.current = window.setTimeout(poll, POLL_INTERVAL_MS)
      } catch (err) {
        if (cancelledRef.current) return
        const { general } = extractApiError(err)
        const message = general ?? 'Não foi possível consultar o status.'
        if (errorNotifiedRef.current !== message) {
          errorNotifiedRef.current = message
          toast.error(message)
        }
        setState((prev) => ({ ...prev, error: message, loading: false }))
        timerRef.current = window.setTimeout(poll, POLL_INTERVAL_MS)
      }
    }

    poll()

    return () => {
      cancelledRef.current = true
      if (timerRef.current !== null) {
        window.clearTimeout(timerRef.current)
        timerRef.current = null
      }
    }
  }, [id, toast])

  useEffect(() => {
    const tick = window.setInterval(() => {
      setElapsedSeconds(
        Math.max(0, Math.floor((Date.now() - startedAtRef.current) / 1000)),
      )
    }, 1000)
    return () => window.clearInterval(tick)
  }, [])

  const currentStatus = state.status?.status ?? null
  const isCelebrating = currentStatus === STATUS_CONCLUIDO
  const videoId: string | null = state.status?.video_id
    ? String(state.status.video_id)
    : (id ?? null)

  useEffect(() => {
    if (!isCelebrating || !videoId) return
    const timer = window.setTimeout(() => {
      navigate(`/analysis/${videoId}`, { replace: true })
    }, CELEBRATION_REDIRECT_MS)
    return () => window.clearTimeout(timer)
  }, [isCelebrating, videoId, navigate])

  const { currentStageIdx, progressPercent, heroStage } = useMemo(() => {
    if (isCelebrating) {
      return {
        currentStageIdx: CELEBRATION_STAGE_INDEX,
        progressPercent: 100,
        heroStage: STATUS_STAGES.length - 1,
      }
    }
    if (!currentStatus) {
      return { currentStageIdx: -1, progressPercent: 0, heroStage: 0 }
    }
    const idx = stageIndexFromStatus(currentStatus)
    return {
      currentStageIdx: idx,
      progressPercent: progressPercentFromStatus(currentStatus),
      heroStage: idx,
    }
  }, [currentStatus, isCelebrating])

  const descricao = state.status?.status_descricao ?? 'Consultando status…'
  const errorMessage = currentStatus ? errorMessageForStatus(currentStatus) : null
  const showError = currentStatus !== null && isErrorStatus(currentStatus)

  if (!id) {
    return (
      <main id="main" tabIndex={-1} className="status-container">
        <h1>Status da análise</h1>
        <ErrorState
          title="Sessão inválida"
          message="O identificador da sessão não foi informado."
          backTo={{ to: '/upload', label: 'Enviar novo vídeo' }}
        />
      </main>
    )
  }

  return (
    <main id="main" tabIndex={-1} className="status-container">
      <h1 className="status-heading">Processando seu vídeo</h1>
      <p className="status-subtitle">Sessão #{id}</p>

      {state.loading && state.status === null ? (
        <LoadingState variant="status" label="Consultando status" />
      ) : null}

      {showError ? (
        <StatusErrorCard message={errorMessage} />
      ) : state.status ? (
        <>
          <section
            className={`status-hero${isCelebrating ? ' status-hero-celebrating' : ''}`}
            aria-label="Progresso da análise"
          >
            <RunnerHero stage={heroStage} isCelebrating={isCelebrating} />
            <div className="status-hero-info">
              <p className="status-hero-elapsed">
                {formatElapsedTime(elapsedSeconds)}
              </p>
              <p className="status-hero-estimate">
                {isCelebrating
                  ? 'Pronto!'
                  : estimatedRemainingLabel(elapsedSeconds)}
              </p>
            </div>
          </section>

          <div
            className="status-progress"
            role="progressbar"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={progressPercent}
            aria-label="Progresso do processamento"
          >
            <div
              className="status-progress-fill"
              style={{
                transform: `scaleX(${progressPercent / 100})`,
              }}
            />
          </div>

          <ol className="status-stepper" aria-label="Etapas do processamento">
            {STATUS_STAGES.map((stage, idx) => {
              const isDone = idx < currentStageIdx
              const isActive = idx === currentStageIdx && !isCelebrating
              const className = [
                'status-stepper-item',
                isDone ? 'status-stepper-item-done' : '',
                isActive ? 'status-stepper-item-active' : '',
              ]
                .filter(Boolean)
                .join(' ')
              return (
                <li
                  key={stage.key}
                  className={className}
                  aria-current={isActive ? 'step' : undefined}
                >
                  <span className="status-stepper-marker" aria-hidden="true">
                    {isDone ? <CheckIcon /> : <span className="status-stepper-dot" />}
                  </span>
                  <span className="status-stepper-label">{stage.label}</span>
                </li>
              )
            })}
          </ol>

          {isCelebrating ? (
            <CelebrationPanel videoId={videoId} />
          ) : (
            <p className="status-current" aria-live="polite">
              {descricao}
            </p>
          )}
        </>
      ) : null}
    </main>
  )
}

function StatusErrorCard({ message }: { message: string | null }) {
  const navigate = useNavigate()
  return (
    <section className="status-error-card" role="alert" aria-live="assertive">
      <Banner
        variant="danger"
        assertive
        title="Não foi possível concluir a análise"
      >
        {message ?? 'Ocorreu um erro inesperado. Tente enviar o vídeo novamente.'}
      </Banner>
      <div className="status-error-actions">
        <Button
          variant="primary"
          size="md"
          onClick={() => navigate('/upload')}
        >
          Enviar novo vídeo
        </Button>
        <Button
          variant="secondary"
          size="md"
          onClick={() => navigate('/upload#dicas')}
        >
          Ver dicas de gravação
        </Button>
      </div>
    </section>
  )
}

function CheckIcon() {
  return (
    <svg
      viewBox="0 0 16 16"
      width="12"
      height="12"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <path
        d="M3 8.5 L6.5 12 L13 5"
        stroke="currentColor"
        strokeWidth="2.25"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function CelebrationPanel({ videoId }: { videoId: string | null }) {
  const navigate = useNavigate()
  return (
    <section className="status-celebration" role="status" aria-live="polite">
      <p className="status-celebration-title">Análise concluída!</p>
      <p className="status-celebration-subtitle">
        Levando você para o diagnóstico…
      </p>
      {videoId ? (
        <Button
          variant="primary"
          size="md"
          className="status-celebration-cta"
          onClick={() => navigate(`/analysis/${videoId}`, { replace: true })}
        >
          Ver diagnóstico
        </Button>
      ) : null}
    </section>
  )
}
