import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './styles/tokens.css'
import './index.css'
import App from './App.tsx'
import { API_BASE_URL } from './api/client'

function preconnectApiOrigin(): void {
  try {
    const apiOrigin = new URL(API_BASE_URL, window.location.origin).origin
    if (apiOrigin === window.location.origin) return
    const head = document.head
    if (head.querySelector(`link[rel="preconnect"][href="${apiOrigin}"]`)) return
    const link = document.createElement('link')
    link.rel = 'preconnect'
    link.href = apiOrigin
    link.crossOrigin = 'anonymous'
    head.appendChild(link)
  } catch {
    // noop — VITE_API_BASE_URL malformed; preconnect is best-effort.
  }
}

preconnectApiOrigin()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
