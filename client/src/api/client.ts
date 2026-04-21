import axios, { type InternalAxiosRequestConfig } from 'axios'

export const TOKEN_STORAGE_KEY = 'running_analyzer_token'

export const API_BASE_URL: string =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_BASE_URL,
})

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem(TOKEN_STORAGE_KEY)
  if (token) {
    config.headers.set('Authorization', `Bearer ${token}`)
  }
  return config
})
