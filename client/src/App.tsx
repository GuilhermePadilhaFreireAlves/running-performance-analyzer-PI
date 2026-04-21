import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { PrivateRoute } from './components/PrivateRoute'
import LoginPage from './pages/LoginPage'
import SignupPage from './pages/SignupPage'
import UploadPage from './pages/UploadPage'
import StatusPage from './pages/StatusPage'
import AnalysisPage from './pages/AnalysisPage'
import AnalysisRawPage from './pages/AnalysisRawPage'
import HistoricoPage from './pages/HistoricoPage'

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route
            path="/upload"
            element={
              <PrivateRoute>
                <UploadPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/status/:id"
            element={
              <PrivateRoute>
                <StatusPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/analysis/:id"
            element={
              <PrivateRoute>
                <AnalysisPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/analysis/:id/raw"
            element={
              <PrivateRoute>
                <AnalysisRawPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/historico"
            element={
              <PrivateRoute>
                <HistoricoPage />
              </PrivateRoute>
            }
          />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
