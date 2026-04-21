import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { TOKEN_STORAGE_KEY } from '../api/client'
import {
  loginRequest,
  signupRequest,
  type LoginPayload,
  type SignupPayload,
  type UserProfile,
} from '../api/auth'

export interface AuthUser {
  id: number
  name?: string
  email?: string
}

export interface AuthContextValue {
  user: AuthUser | null
  token: string | null
  isAuthenticated: boolean
  login: (payload: LoginPayload) => Promise<void>
  signup: (payload: SignupPayload) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

function decodeTokenSubject(token: string): number | null {
  const parts = token.split('.')
  if (parts.length !== 3) return null
  try {
    const payload = parts[1]
    const normalized = payload.replace(/-/g, '+').replace(/_/g, '/')
    const padded = normalized + '='.repeat((4 - (normalized.length % 4)) % 4)
    const decoded = atob(padded)
    const claims = JSON.parse(decoded) as { sub?: string | number }
    if (claims.sub === undefined || claims.sub === null) return null
    const parsed = typeof claims.sub === 'number' ? claims.sub : Number.parseInt(claims.sub, 10)
    return Number.isFinite(parsed) ? parsed : null
  } catch {
    return null
  }
}

function userFromToken(token: string): AuthUser | null {
  const id = decodeTokenSubject(token)
  return id === null ? null : { id }
}

function userFromProfile(profile: UserProfile): AuthUser {
  return { id: profile.id, name: profile.name, email: profile.email }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() =>
    localStorage.getItem(TOKEN_STORAGE_KEY),
  )
  const [user, setUser] = useState<AuthUser | null>(() => {
    const stored = localStorage.getItem(TOKEN_STORAGE_KEY)
    return stored ? userFromToken(stored) : null
  })

  useEffect(() => {
    if (token === null) {
      localStorage.removeItem(TOKEN_STORAGE_KEY)
    } else {
      localStorage.setItem(TOKEN_STORAGE_KEY, token)
    }
  }, [token])

  const login = useCallback(async (payload: LoginPayload) => {
    const { access_token } = await loginRequest(payload)
    setToken(access_token)
    setUser(userFromToken(access_token))
  }, [])

  const signup = useCallback(async (payload: SignupPayload) => {
    const profile = await signupRequest(payload)
    const { access_token } = await loginRequest({ email: payload.email, senha: payload.senha })
    setToken(access_token)
    setUser(userFromProfile(profile))
  }, [])

  const logout = useCallback(() => {
    setToken(null)
    setUser(null)
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      isAuthenticated: token !== null,
      login,
      signup,
      logout,
    }),
    [user, token, login, signup, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (ctx === null) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return ctx
}
