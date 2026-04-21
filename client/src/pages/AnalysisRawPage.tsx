import { useParams } from 'react-router-dom'

export default function AnalysisRawPage() {
  const { id } = useParams<{ id: string }>()
  return (
    <main>
      <h1>Dados biomecânicos brutos</h1>
      <p>Sessão: {id ?? '—'}. Séries por frame — US-026.</p>
    </main>
  )
}
