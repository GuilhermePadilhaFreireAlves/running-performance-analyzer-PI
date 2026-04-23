import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import type { ReactElement } from 'react'
import { AuthProvider } from './context/AuthContext'
import { PrivateRoute } from './components/PrivateRoute'
import { AppShell } from './components/AppShell'
import LoginPage from './pages/LoginPage'
import SignupPage from './pages/SignupPage'
import UploadPage from './pages/UploadPage'
import StatusPage from './pages/StatusPage'
import AnalysisPage from './pages/AnalysisPage'
import AnalysisRawPage from './pages/AnalysisRawPage'
import HistoricoPage from './pages/HistoricoPage'

function privateElement(node: ReactElement): ReactElement {
  return (
    <PrivateRoute>
      <AppShell>{node}</AppShell>
    </PrivateRoute>
  )
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route path="/upload" element={privateElement(<UploadPage />)} />
          <Route path="/status/:id" element={privateElement(<StatusPage />)} />
          <Route path="/analysis/:id" element={privateElement(<AnalysisPage />)} />
          <Route path="/analysis/:id/raw" element={privateElement(<AnalysisRawPage />)} />
          <Route path="/historico" element={privateElement(<HistoricoPage />)} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
