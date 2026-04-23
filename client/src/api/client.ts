import axios from 'axios'
import type { AxiosError, InternalAxiosRequestConfig } from 'axios'

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

type UnauthorizedHandler = () => void

let unauthorizedHandler: UnauthorizedHandler | null = null

export function setUnauthorizedHandler(handler: UnauthorizedHandler | null): void {
  unauthorizedHandler = handler
}

const AUTH_PATHS = ['/api/auth/login', '/api/users/register']

function isAuthEndpoint(url: string | undefined): boolean {
  if (!url) return false
  return AUTH_PATHS.some((path) => url.includes(path))
}

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (
      error.response?.status === 401 &&
      unauthorizedHandler !== null &&
      !isAuthEndpoint(error.config?.url)
    ) {
      unauthorizedHandler()
    }
    return Promise.reject(error)
  },
)
