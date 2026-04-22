import { api } from './client'

export interface HistoricoItem {
  id: number
  criado_em: string
  pace_min_km: number | null
  status: string
  nota_geral: number | null
}

export interface HistoricoResponse {
  items: HistoricoItem[]
  total: number
  page: number
  limit: number
}

export interface HistoricoParams {
  page?: number
  limit?: number
}

export async function getHistoricoRequest(
  params: HistoricoParams = {},
): Promise<HistoricoResponse> {
  const { data } = await api.get<HistoricoResponse>('/api/historico-analise', {
    params: {
      page: params.page,
      limit: params.limit,
    },
  })
  return data
}
