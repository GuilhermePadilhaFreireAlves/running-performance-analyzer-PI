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

export interface RawFrame {
  frame_idx: number
  keypoints: (number[] | null)[]
  angulo_joelho_esq: number | null
  angulo_joelho_dir: number | null
  angulo_cotovelo_esq: number | null
  angulo_cotovelo_dir: number | null
  inclinacao_tronco: number | null
  y_com: number | null
}

export interface SimetriaRawResponse {
  tcs: number | null
  joelho: number | null
  oscilacao: number | null
}

export interface AnalysisRawResponse {
  fps: number | null
  frames: RawFrame[]
  metricas_agregadas: MetricaResumida[]
  simetria: SimetriaRawResponse
  erro: string | null
}

export async function getRawAnalysisRequest(
  analysisId: number | string,
): Promise<AnalysisRawResponse> {
  const { data } = await api.get<AnalysisRawResponse>(
    `/api/analysis/${analysisId}/raw`,
  )
  return data
}
