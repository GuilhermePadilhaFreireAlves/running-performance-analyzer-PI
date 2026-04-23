import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { setUnauthorizedHandler } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'

/**
 * Registra no cliente HTTP o handler global de 401: exibe toast de "Sessão
 * expirada", limpa o token via logout() e redireciona para /login. O
 * interceptor em api/client.ts pula esse handler em chamadas para endpoints
 * de auth (login/register), então erros de credenciais continuam sendo
 * tratados localmente nos próprios formulários.
 */
export function UnauthorizedBridge() {
  const navigate = useNavigate()
  const { logout } = useAuth()
  const toast = useToast()

  useEffect(() => {
    setUnauthorizedHandler(() => {
      toast.error('Sessão expirada')
      logout()
      navigate('/login', { replace: true })
    })
    return () => {
      setUnauthorizedHandler(null)
    }
  }, [navigate, logout, toast])

  return null
}
