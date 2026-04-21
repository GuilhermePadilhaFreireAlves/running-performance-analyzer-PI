import { useParams } from 'react-router-dom'

export default function StatusPage() {
  const { id } = useParams<{ id: string }>()
  return (
    <main>
      <h1>Status da análise</h1>
      <p>Sessão: {id ?? '—'}. Tela de polling — US-024.</p>
    </main>
  )
}
