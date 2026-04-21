import { api } from './client'

export interface LoginPayload {
  email: string
  senha: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
}

export interface SignupPayload {
  name: string
  email: string
  senha: string
  altura_cm: number
  peso_kg?: number | null
  nivel_experiencia?: string | null
}

export interface UserProfile {
  id: number
  name: string
  email: string
  altura_cm: number
  peso_kg: number | null
  nivel_experiencia: string | null
}

export async function loginRequest(payload: LoginPayload): Promise<LoginResponse> {
  const { data } = await api.post<LoginResponse>('/api/auth/login', payload)
  return data
}

export async function signupRequest(payload: SignupPayload): Promise<UserProfile> {
  const { data } = await api.post<UserProfile>('/api/users/register', payload)
  return data
}
