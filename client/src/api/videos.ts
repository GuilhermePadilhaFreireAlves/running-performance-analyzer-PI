import { api } from './client'

export interface VideoUploadResponse {
  video_id: number
  status: string
}

export interface VideoUploadParams {
  file: File
  paceMinKm: number
}

export async function uploadVideoRequest(
  params: VideoUploadParams,
): Promise<VideoUploadResponse> {
  const formData = new FormData()
  formData.append('file', params.file)
  formData.append('pace_min_km', params.paceMinKm.toString())
  const { data } = await api.post<VideoUploadResponse>(
    '/api/videos/upload',
    formData,
  )
  return data
}

export interface VideoStatusResponse {
  video_id: number
  status: string
  status_descricao: string
}

export async function getVideoStatusRequest(
  videoId: number | string,
): Promise<VideoStatusResponse> {
  const { data } = await api.get<VideoStatusResponse>(
    `/api/videos/${videoId}/status`,
  )
  return data
}
