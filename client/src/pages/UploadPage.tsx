import { useState } from 'react'
import { PaceInput } from '../components/PaceInput'
import type { PaceInputValue } from '../components/PaceInput'

export default function UploadPage() {
  const [pace, setPace] = useState<PaceInputValue>({
    paceMinKm: null,
    isValid: false,
    errorMessage: null,
  })

  const canSubmit = pace.isValid

  return (
    <main className="auth-container">
      <h1>Upload de vídeo</h1>
      <form
        className="auth-form"
        noValidate
        onSubmit={(event) => event.preventDefault()}
        aria-label="Formulário de upload"
      >
        <PaceInput onChange={setPace} />
        <button type="submit" disabled={!canSubmit}>
          {canSubmit
            ? `Enviar vídeo (pace ${pace.paceMinKm?.toFixed(2)} min/km)`
            : 'Selecione vídeo e pace válido — US-023'}
        </button>
      </form>
    </main>
  )
}
