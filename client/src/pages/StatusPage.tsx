import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { getVideoStatusRequest } from '../api/videos'
import type { VideoStatusResponse } from '../api/videos'
import { extractApiError } from '../api/errors'
import {
  STATUS_STAGES,
  errorMessageForStatus,
  isErrorStatus,
  isFinalStatus,
  progressPercentFromStatus,
  stageIndexFromStatus,
  STATUS_CONCLUIDO,
} from '../utils/videoStatus'

const POLL_INTERVAL_MS = 2000

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
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [state, setState] = useState<FetchState>(INITIAL_STATE)
  const timerRef = useRef<number | null>(null)
  const cancelledRef = useRef(false)

  useEffect(() => {
    if (!id) return
    cancelledRef.current = false

    const poll = async () => {
      try {
        const data = await getVideoStatusRequest(id)
        if (cancelledRef.current) return
        setState({ status: data, error: null, loading: false })
        if (data.status === STATUS_CONCLUIDO) {
          cancelledRef.current = true
          navigate(`/analysis/${data.video_id}`, { replace: true })
          return
        }
        if (isFinalStatus(data.status)) {
          cancelledRef.current = true
          return
        }
        timerRef.current = window.setTimeout(poll, POLL_INTERVAL_MS)
      } catch (err) {
        if (cancelledRef.current) return
        const { general } = extractApiError(err)
        setState({
          status: null,
          error: general ?? 'Não foi possível consultar o status.',
          loading: false,
        })
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
  }, [id, navigate])

  if (!id) {
    return (
      <main className="auth-container">
        <h1>Status da análise</h1>
        <p className="form-error" role="alert">
          Sessão inválida — identificador ausente.
        </p>
      </main>
    )
  }

  const status = state.status?.status ?? null
  const descricao = state.status?.status_descricao ?? 'Carregando…'
  const currentStageIdx = status ? stageIndexFromStatus(status) : -1
  const progressPercent = status ? progressPercentFromStatus(status) : 0
  const errorMessage = status ? errorMessageForStatus(status) : null
  const showError = status !== null && isErrorStatus(status)

  return (
    <main className="auth-container status-container">
      <h1>Processando seu vídeo</h1>
      <p className="status-subtitle">Sessão #{id}</p>

      {state.loading && state.status === null ? (
        <p className="upload-info">Consultando status…</p>
      ) : null}

      {showError && errorMessage ? (
        <div className="status-error" role="alert">
          <p className="form-error">{errorMessage}</p>
          <button
            type="button"
            className="status-restart-button"
            onClick={() => navigate('/upload')}
          >
            Enviar novo vídeo
          </button>
        </div>
      ) : (
        <>
          <div
            className="status-progress"
            role="progressbar"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={progressPercent}
            aria-label="Progresso do processamento"
          >
            <div
              className="status-progress-bar"
              style={{ width: `${progressPercent}%` }}
            />
          </div>

          <ol className="status-stage-list">
            {STATUS_STAGES.map((stage, idx) => {
              const isDone = idx < currentStageIdx
              const isActive = idx === currentStageIdx
              const className = [
                'status-stage',
                isDone ? 'status-stage-done' : '',
                isActive ? 'status-stage-active' : '',
              ]
                .filter(Boolean)
                .join(' ')
              return (
                <li
                  key={stage.key}
                  className={className}
                  aria-current={isActive ? 'step' : undefined}
                >
                  <span className="status-stage-marker" aria-hidden="true" />
                  <span className="status-stage-label">{stage.label}</span>
                </li>
              )
            })}
          </ol>

          <p className="status-current" aria-live="polite">
            {descricao}
          </p>

          {state.error ? (
            <p className="form-error" role="alert">
              {state.error}
            </p>
          ) : null}
        </>
      )}
    </main>
  )
}
