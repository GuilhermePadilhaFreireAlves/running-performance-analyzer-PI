import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { ChangeEvent, DragEvent, FormEvent, KeyboardEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { uploadVideoRequest } from '../api/videos'
import { extractApiError } from '../api/errors'
import { PaceInput } from '../components/PaceInput'
import type { PaceInputValue } from '../components/PaceInput'
import { readVideoMetadata } from '../utils/videoMeta'
import {
  VIDEO_LOW_FPS_WARNING,
  VIDEO_LOW_QUALITY_MESSAGE,
  VIDEO_MAX_DURATION_SEC,
  VIDEO_MIN_DURATION_SEC,
  VIDEO_MIN_FPS,
  VIDEO_MIN_HEIGHT,
  VIDEO_MIN_WIDTH,
  VIDEO_TOO_LONG_MESSAGE,
  VIDEO_TOO_SHORT_MESSAGE,
  validateVideoMetadata,
} from '../utils/videoValidation'
import type {
  VideoMetadata,
  VideoValidationResult,
} from '../utils/videoValidation'
import { usePageTitle } from '../hooks/usePageTitle'
import { useToast } from '../context/ToastContext'
import { Banner, Button } from '../components/ui'

type CheckStatus = 'pending' | 'pass' | 'fail' | 'warn'

interface ChecklistItem {
  id: string
  label: string
  status: CheckStatus
  detail: string
}

interface VideoState {
  file: File | null
  metadata: VideoMetadata | null
  validation: VideoValidationResult | null
  previewUrl: string | null
  loading: boolean
  readError: string | null
}

const EMPTY_PACE: PaceInputValue = {
  paceMinKm: null,
  isValid: false,
  errorMessage: null,
}

const EMPTY_VIDEO: VideoState = {
  file: null,
  metadata: null,
  validation: null,
  previewUrl: null,
  loading: false,
  readError: null,
}

function formatDuration(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds <= 0) return '—'
  if (seconds < 60) return `${seconds.toFixed(1)}s`
  const min = Math.floor(seconds / 60)
  const sec = Math.round(seconds - min * 60)
  return `${min}min${sec.toString().padStart(2, '0')}s`
}

function buildChecklist(
  video: VideoState,
): ChecklistItem[] {
  const { metadata, validation, loading, readError, file } = video

  const makePending = (
    id: string,
    label: string,
    detail: string,
  ): ChecklistItem => ({ id, label, status: 'pending', detail })

  if (!file) {
    return [
      makePending('duracao', 'Duração', 'Aguardando vídeo'),
      makePending('resolucao', 'Resolução', 'Aguardando vídeo'),
      makePending('fps', 'FPS', 'Aguardando vídeo'),
      makePending(
        'perspectiva',
        'Perspectiva lateral',
        'Validado pelo servidor após envio',
      ),
    ]
  }

  if (loading) {
    return [
      makePending('duracao', 'Duração', 'Lendo metadados…'),
      makePending('resolucao', 'Resolução', 'Lendo metadados…'),
      makePending('fps', 'FPS', 'Lendo metadados…'),
      makePending(
        'perspectiva',
        'Perspectiva lateral',
        'Validado pelo servidor após envio',
      ),
    ]
  }

  if (readError || !metadata || !validation) {
    return [
      {
        id: 'duracao',
        label: 'Duração',
        status: 'fail',
        detail: readError ?? 'Não foi possível ler o vídeo',
      },
      makePending('resolucao', 'Resolução', '—'),
      makePending('fps', 'FPS', '—'),
      makePending(
        'perspectiva',
        'Perspectiva lateral',
        'Validado pelo servidor após envio',
      ),
    ]
  }

  const duration = metadata.durationSec
  let duracaoStatus: CheckStatus = 'pass'
  let duracaoDetail = `${formatDuration(duration)} · mínimo ${VIDEO_MIN_DURATION_SEC}s, máximo ${VIDEO_MAX_DURATION_SEC}s`
  if (!Number.isFinite(duration) || duration < VIDEO_MIN_DURATION_SEC) {
    duracaoStatus = 'fail'
    duracaoDetail = VIDEO_TOO_SHORT_MESSAGE
  } else if (duration > VIDEO_MAX_DURATION_SEC) {
    duracaoStatus = 'fail'
    duracaoDetail = VIDEO_TOO_LONG_MESSAGE
  }

  const { width, height } = metadata
  let resolucaoStatus: CheckStatus = 'pass'
  let resolucaoDetail = `${width}×${height} · mínimo ${VIDEO_MIN_WIDTH}×${VIDEO_MIN_HEIGHT}`
  if (width < VIDEO_MIN_WIDTH || height < VIDEO_MIN_HEIGHT) {
    resolucaoStatus = 'fail'
    resolucaoDetail = VIDEO_LOW_QUALITY_MESSAGE
  }

  const fps = metadata.estimatedFps
  let fpsStatus: CheckStatus
  let fpsDetail: string
  if (fps === null) {
    fpsStatus = 'pending'
    fpsDetail = `FPS não pôde ser estimado no navegador. Servidor exige ≥ ${VIDEO_MIN_FPS} FPS.`
  } else if (fps < VIDEO_MIN_FPS) {
    fpsStatus = 'warn'
    fpsDetail = `FPS estimado ${fps.toFixed(1)} · ${VIDEO_LOW_FPS_WARNING}`
  } else {
    fpsStatus = 'pass'
    fpsDetail = `FPS estimado ${fps.toFixed(1)}`
  }

  return [
    {
      id: 'duracao',
      label: 'Duração',
      status: duracaoStatus,
      detail: duracaoDetail,
    },
    {
      id: 'resolucao',
      label: 'Resolução',
      status: resolucaoStatus,
      detail: resolucaoDetail,
    },
    { id: 'fps', label: 'FPS', status: fpsStatus, detail: fpsDetail },
    {
      id: 'perspectiva',
      label: 'Perspectiva lateral',
      status: 'pending',
      detail: 'Validado pelo servidor após envio',
    },
  ]
}

function statusSymbol(status: CheckStatus): string {
  switch (status) {
    case 'pass':
      return '✓'
    case 'fail':
      return '✕'
    case 'warn':
      return '!'
    case 'pending':
    default:
      return '…'
  }
}

export default function UploadPage() {
  usePageTitle('Nova análise')
  const [pace, setPace] = useState<PaceInputValue>(EMPTY_PACE)
  const [video, setVideo] = useState<VideoState>(EMPTY_VIDEO)
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [progressPercent, setProgressPercent] = useState<number | null>(null)
  const [isDragActive, setIsDragActive] = useState(false)
  const [hintOpen, setHintOpen] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const navigate = useNavigate()
  const toast = useToast()

  useEffect(() => {
    return () => {
      if (video.previewUrl) URL.revokeObjectURL(video.previewUrl)
    }
  }, [video.previewUrl])

  const handlePaceChange = useCallback((next: PaceInputValue) => {
    setPace(next)
  }, [])

  const processFile = useCallback(async (file: File) => {
    setSubmitError(null)
    const previousPreview = video.previewUrl
    const nextPreview = URL.createObjectURL(file)
    setVideo({
      file,
      metadata: null,
      validation: null,
      previewUrl: nextPreview,
      loading: true,
      readError: null,
    })
    if (previousPreview) URL.revokeObjectURL(previousPreview)
    try {
      const metadata = await readVideoMetadata(file)
      const validation = validateVideoMetadata(metadata)
      setVideo({
        file,
        metadata,
        validation,
        previewUrl: nextPreview,
        loading: false,
        readError: null,
      })
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : 'Não foi possível ler metadados do vídeo.'
      setVideo({
        file,
        metadata: null,
        validation: null,
        previewUrl: nextPreview,
        loading: false,
        readError: message,
      })
    }
  }, [video.previewUrl])

  const handleFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] ?? null
    if (!file) return
    await processFile(file)
  }

  const openFilePicker = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  const handleDropzoneKey = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      openFilePicker()
    }
  }

  const handleDragOver = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    event.stopPropagation()
    if (submitting) return
    if (!isDragActive) setIsDragActive(true)
  }

  const handleDragLeave = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    event.stopPropagation()
    setIsDragActive(false)
  }

  const handleDrop = async (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    event.stopPropagation()
    setIsDragActive(false)
    if (submitting) return
    const files = event.dataTransfer?.files
    if (!files || files.length === 0) return
    const file = files[0]
    if (!file.type.startsWith('video/')) {
      setSubmitError(
        'Arquivo inválido — arraste um vídeo (mp4, mov, webm, etc.).',
      )
      return
    }
    await processFile(file)
  }

  const checklist = useMemo(() => buildChecklist(video), [video])

  const canSubmit =
    !submitting &&
    !video.loading &&
    video.file !== null &&
    video.validation !== null &&
    video.validation.isValid &&
    pace.isValid &&
    pace.paceMinKm !== null

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (
      submitting ||
      !video.file ||
      !video.validation?.isValid ||
      !pace.isValid ||
      pace.paceMinKm === null
    ) {
      return
    }
    setSubmitting(true)
    setSubmitError(null)
    setProgressPercent(0)
    try {
      const response = await uploadVideoRequest({
        file: video.file,
        paceMinKm: pace.paceMinKm,
        onProgress: (percent) => setProgressPercent(percent),
      })
      toast.success('Vídeo enviado. Iniciando análise.')
      navigate(`/status/${response.video_id}`)
    } catch (err) {
      const { general } = extractApiError(err)
      setSubmitError(general ?? 'Erro ao enviar vídeo. Tente novamente.')
      setProgressPercent(null)
    } finally {
      setSubmitting(false)
    }
  }

  const dropzoneClass = [
    'upload-dropzone',
    isDragActive ? 'is-drag-active' : '',
    video.file ? 'has-file' : '',
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <main id="main" tabIndex={-1} className="upload-page">
      <header className="upload-page-header">
        <h1>Nova análise</h1>
        <p className="upload-page-subtitle">
          Envie um vídeo lateral da sua corrida e informe o pace para
          recebermos uma análise biomecânica.
        </p>
      </header>

      <form
        className="upload-form"
        noValidate
        onSubmit={handleSubmit}
        aria-label="Formulário de upload"
      >
        <div className="upload-layout">
          <div
            className={dropzoneClass}
            role="button"
            tabIndex={0}
            aria-label="Arraste um vídeo aqui ou clique para selecionar"
            aria-disabled={submitting ? 'true' : 'false'}
            onClick={() => {
              if (!submitting) openFilePicker()
            }}
            onKeyDown={handleDropzoneKey}
            onDragOver={handleDragOver}
            onDragEnter={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="video/*"
              onChange={handleFileChange}
              disabled={submitting}
              className="upload-file-input"
              aria-hidden="true"
              tabIndex={-1}
            />
            {video.previewUrl ? (
              <video
                className="upload-preview"
                src={video.previewUrl}
                preload="metadata"
                muted
                playsInline
                controls
                aria-label="Preview do vídeo selecionado"
              />
            ) : (
              <div className="upload-dropzone-empty" aria-hidden="true">
                <svg
                  className="upload-dropzone-icon"
                  viewBox="0 0 48 48"
                  width="40"
                  height="40"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M24 32V12" />
                  <path d="M16 20l8-8 8 8" />
                  <path d="M10 34v4a2 2 0 0 0 2 2h24a2 2 0 0 0 2-2v-4" />
                </svg>
                <p className="upload-dropzone-title">
                  Arraste o vídeo ou clique para selecionar
                </p>
                <p className="upload-dropzone-hint">
                  MP4, MOV ou WebM · até {VIDEO_MAX_DURATION_SEC / 60} min
                </p>
              </div>
            )}
            {video.file ? (
              <p className="upload-file-name">{video.file.name}</p>
            ) : null}
          </div>

          <aside className="upload-checklist" aria-label="Validações do vídeo">
            <h2 className="upload-checklist-title">Validações</h2>
            <ul className="upload-checklist-list">
              {checklist.map((item) => (
                <li
                  key={item.id}
                  className={`upload-check upload-check-${item.status}`}
                >
                  <span
                    className="upload-check-icon"
                    aria-hidden="true"
                  >
                    {statusSymbol(item.status)}
                  </span>
                  <div className="upload-check-body">
                    <p className="upload-check-label">{item.label}</p>
                    <p className="upload-check-detail">{item.detail}</p>
                  </div>
                </li>
              ))}
            </ul>
          </aside>
        </div>

        <PaceInput onChange={handlePaceChange} />

        <details
          id="dicas"
          className="upload-hint"
          open={hintOpen}
          onToggle={(event) =>
            setHintOpen((event.target as HTMLDetailsElement).open)
          }
        >
          <summary>Como gravar o vídeo ideal</summary>
          <ul>
            <li>Grave de lado (perspectiva lateral), com a câmera parada.</li>
            <li>Use 60 FPS ou mais para precisão do cálculo biomecânico.</li>
            <li>Grave pelo menos 30 segundos de corrida contínua.</li>
            <li>
              Enquadre o corredor inteiro, sem que ele saia do quadro durante a
              corrida.
            </li>
            <li>Resolução mínima 480p (ideal 720p ou mais).</li>
          </ul>
        </details>

        {submitError ? (
          <Banner variant="danger" assertive title="Não foi possível enviar">
            {submitError} Ajuste o vídeo seguindo as dicas acima e tente
            novamente.
          </Banner>
        ) : null}

        {submitting && progressPercent !== null ? (
          <div
            className="upload-progress"
            role="progressbar"
            aria-label="Progresso do upload"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={progressPercent}
          >
            <div
              className="upload-progress-bar"
              style={{ transform: `scaleX(${progressPercent / 100})` }}
            />
            <span className="upload-progress-label">
              Enviando… {progressPercent}%
            </span>
          </div>
        ) : null}

        <Button
          type="submit"
          size="lg"
          loading={submitting}
          disabled={!canSubmit}
          className="upload-submit"
        >
          Analisar corrida
        </Button>
      </form>
    </main>
  )
}
