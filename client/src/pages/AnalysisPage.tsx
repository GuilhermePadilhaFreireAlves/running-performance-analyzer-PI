import { useParams } from 'react-router-dom'

export default function AnalysisPage() {
  const { id } = useParams<{ id: string }>()
  return (
    <main>
      <h1>Diagnóstico simplificado</h1>
      <p>Sessão: {id ?? '—'}. Tela simplificada — US-025.</p>
    </main>
  )
}
