import { Navigate, useLocation } from 'react-router-dom'
import type { ReactElement } from 'react'
import { useAuth } from '../context/AuthContext'

interface PrivateRouteProps {
  children: ReactElement
}

export function PrivateRoute({ children }: PrivateRouteProps) {
  const { isAuthenticated } = useAuth()
  const location = useLocation()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  return children
}
