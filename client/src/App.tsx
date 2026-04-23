import { BrowserRouter, Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { lazy, Suspense } from 'react'
import type { ReactElement } from 'react'
import { AuthProvider } from './context/AuthContext'
import { ToastProvider } from './context/ToastContext'
import { PrivateRoute } from './components/PrivateRoute'
import { AppShell } from './components/AppShell'
import { UnauthorizedBridge } from './components/UnauthorizedBridge'
import { LoadingState } from './components/ui'
import type { LoadingVariant } from './components/ui'
import LoginPage from './pages/LoginPage'
import SignupPage from './pages/SignupPage'

const UploadPage = lazy(() => import('./pages/UploadPage'))
const StatusPage = lazy(() => import('./pages/StatusPage'))
const AnalysisPage = lazy(() => import('./pages/AnalysisPage'))
const AnalysisRawPage = lazy(() => import('./pages/AnalysisRawPage'))
const HistoricoPage = lazy(() => import('./pages/HistoricoPage'))

function privateElement(node: ReactElement, variant: LoadingVariant): ReactElement {
  return (
    <PrivateRoute>
      <AppShell>
        <Suspense fallback={<LoadingState variant={variant} />}>{node}</Suspense>
      </AppShell>
    </PrivateRoute>
  )
}

function RoutedApp() {
  const location = useLocation()
  return (
    <div className="route-fade" key={location.pathname}>
      <Routes location={location}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/upload" element={privateElement(<UploadPage />, 'status')} />
        <Route path="/status/:id" element={privateElement(<StatusPage />, 'status')} />
        <Route path="/analysis/:id" element={privateElement(<AnalysisPage />, 'analysis')} />
        <Route
          path="/analysis/:id/raw"
          element={privateElement(<AnalysisRawPage />, 'analysis-raw')}
        />
        <Route path="/historico" element={privateElement(<HistoricoPage />, 'historico')} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </div>
  )
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <ToastProvider>
          <UnauthorizedBridge />
          <a className="skip-link" href="#main">
            Pular para o conteúdo
          </a>
          <RoutedApp />
        </ToastProvider>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
