import { api } from './client'

export interface RecomendacaoResponse {
  categoria: string
  descricao: string
  severidade: string
}

export interface MetricaResumida {
  tipo: string
  valor: number | null
  unidade: string | null
}

export interface AnalysisSimpleResponse {
  nota_geral: number | null
  feedback_ia: string | null
  recomendacoes: RecomendacaoResponse[]
  metricas_resumidas: MetricaResumida[]
  erro: string | null
}

export async function getSimpleAnalysisRequest(
  analysisId: number | string,
): Promise<AnalysisSimpleResponse> {
  const { data } = await api.get<AnalysisSimpleResponse>(
    `/api/analysis/${analysisId}/simple`,
  )
  return data
}
