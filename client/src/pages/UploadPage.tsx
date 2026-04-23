import { useCallback, useState } from 'react'
import type { ChangeEvent, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { uploadVideoRequest } from '../api/videos'
import { extractApiError } from '../api/errors'
import { PaceInput } from '../components/PaceInput'
import type { PaceInputValue } from '../components/PaceInput'
import { readVideoMetadata } from '../utils/videoMeta'
import { validateVideoMetadata } from '../utils/videoValidation'
import type {
  VideoMetadata,
  VideoValidationResult,
} from '../utils/videoValidation'
import { usePageTitle } from '../hooks/usePageTitle'

interface VideoState {
  file: File | null
  metadata: VideoMetadata | null
  validation: VideoValidationResult | null
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
  loading: false,
  readError: null,
}

export default function UploadPage() {
  usePageTitle('Nova análise')
  const [pace, setPace] = useState<PaceInputValue>(EMPTY_PACE)
  const [video, setVideo] = useState<VideoState>(EMPTY_VIDEO)
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const navigate = useNavigate()

  const handlePaceChange = useCallback((next: PaceInputValue) => {
    setPace(next)
  }, [])

  const handleFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
    setSubmitError(null)
    const file = event.target.files?.[0] ?? null
    if (!file) {
      setVideo(EMPTY_VIDEO)
      return
    }
    setVideo({
      file,
      metadata: null,
      validation: null,
      loading: true,
      readError: null,
    })
    try {
      const metadata = await readVideoMetadata(file)
      const validation = validateVideoMetadata(metadata)
      setVideo({
        file,
        metadata,
        validation,
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
        loading: false,
        readError: message,
      })
    }
  }

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
    try {
      const response = await uploadVideoRequest({
        file: video.file,
        paceMinKm: pace.paceMinKm,
      })
      navigate(`/status/${response.video_id}`)
    } catch (err) {
      const { general } = extractApiError(err)
      setSubmitError(general ?? 'Erro ao enviar vídeo. Tente novamente.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main id="main" tabIndex={-1} className="auth-container">
      <h1>Upload de vídeo</h1>
      <form
        className="auth-form"
        noValidate
        onSubmit={handleSubmit}
        aria-label="Formulário de upload"
      >
        <label className="field">
          <span>Vídeo (lateral, 30s–3min, ≥ 480p, idealmente ≥ 60 FPS)</span>
          <input
            type="file"
            accept="video/*"
            onChange={handleFileChange}
            disabled={submitting}
            aria-invalid={
              video.validation && !video.validation.isValid ? 'true' : 'false'
            }
          />
        </label>

        {video.loading ? (
          <p className="upload-info">Lendo metadados do vídeo…</p>
        ) : null}

        {video.metadata !== null ? (
          <p className="upload-meta-summary">
            Duração: {video.metadata.durationSec.toFixed(1)}s · Resolução:{' '}
            {video.metadata.width}×{video.metadata.height}
            {video.metadata.estimatedFps !== null
              ? ` · FPS estimado: ${video.metadata.estimatedFps.toFixed(1)}`
              : ''}
          </p>
        ) : null}

        {video.readError ? (
          <p className="field-error" role="alert">
            {video.readError}
          </p>
        ) : null}

        {video.validation &&
        !video.validation.isValid &&
        video.validation.errorMessage ? (
          <p className="field-error" role="alert">
            {video.validation.errorMessage}
          </p>
        ) : null}

        {video.validation?.warnings.map((warning) => (
          <p className="upload-warning" key={warning} role="status">
            {warning}
          </p>
        ))}

        <PaceInput onChange={handlePaceChange} />

        {submitError ? (
          <p className="form-error" role="alert">
            {submitError}
          </p>
        ) : null}

        <button type="submit" disabled={!canSubmit}>
          {submitting ? 'Enviando…' : 'Enviar vídeo'}
        </button>
      </form>
    </main>
  )
}
