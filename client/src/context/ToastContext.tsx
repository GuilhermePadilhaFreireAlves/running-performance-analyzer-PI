import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react'
import type { ReactNode } from 'react'
import { createPortal } from 'react-dom'

export type ToastVariant = 'success' | 'error' | 'info'

export interface ToastOptions {
  duration?: number
  assertive?: boolean
}

interface ToastItem {
  id: string
  variant: ToastVariant
  message: string
  duration: number
  assertive: boolean
}

export interface ToastApi {
  success: (message: string, options?: ToastOptions) => string
  error: (message: string, options?: ToastOptions) => string
  info: (message: string, options?: ToastOptions) => string
  dismiss: (id: string) => void
}

export const TOAST_DEFAULT_DURATION_MS = 5000

const ToastContext = createContext<ToastApi | null>(null)

let toastIdCounter = 0
function nextToastId(): string {
  toastIdCounter += 1
  return `toast-${toastIdCounter}`
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([])

  const dismiss = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  const push = useCallback(
    (variant: ToastVariant, message: string, options?: ToastOptions): string => {
      const id = nextToastId()
      const duration = options?.duration ?? TOAST_DEFAULT_DURATION_MS
      const assertive = options?.assertive ?? variant === 'error'
      setToasts((prev) => [...prev, { id, variant, message, duration, assertive }])
      return id
    },
    [],
  )

  const api = useMemo<ToastApi>(
    () => ({
      success: (msg, opts) => push('success', msg, opts),
      error: (msg, opts) => push('error', msg, opts),
      info: (msg, opts) => push('info', msg, opts),
      dismiss,
    }),
    [push, dismiss],
  )

  return (
    <ToastContext.Provider value={api}>
      {children}
      <ToastRegion toasts={toasts} onDismiss={dismiss} />
    </ToastContext.Provider>
  )
}

export function useToast(): ToastApi {
  const ctx = useContext(ToastContext)
  if (ctx === null) {
    throw new Error('useToast must be used within a ToastProvider')
  }
  return ctx
}

interface ToastRegionProps {
  toasts: ToastItem[]
  onDismiss: (id: string) => void
}

function ToastRegion({ toasts, onDismiss }: ToastRegionProps) {
  if (typeof document === 'undefined') return null

  const polite = toasts.filter((t) => !t.assertive)
  const assertive = toasts.filter((t) => t.assertive)

  return createPortal(
    <div className="toast-region" aria-label="Notificações">
      <div
        className="toast-stack"
        aria-live="polite"
        aria-relevant="additions"
        aria-atomic="false"
      >
        {polite.map((item) => (
          <ToastCard key={item.id} item={item} onDismiss={onDismiss} />
        ))}
      </div>
      <div
        className="toast-stack"
        aria-live="assertive"
        aria-relevant="additions"
        aria-atomic="false"
      >
        {assertive.map((item) => (
          <ToastCard key={item.id} item={item} onDismiss={onDismiss} />
        ))}
      </div>
    </div>,
    document.body,
  )
}

interface ToastCardProps {
  item: ToastItem
  onDismiss: (id: string) => void
}

const TOAST_ICON: Record<ToastVariant, string> = {
  success: '✓',
  error: '!',
  info: 'i',
}

function ToastCard({ item, onDismiss }: ToastCardProps) {
  const timerRef = useRef<number | null>(null)
  const remainingRef = useRef<number>(item.duration)
  const startRef = useRef<number>(Date.now())
  const [entered, setEntered] = useState(false)

  const clearTimer = useCallback(() => {
    if (timerRef.current !== null) {
      window.clearTimeout(timerRef.current)
      timerRef.current = null
    }
  }, [])

  const schedule = useCallback(
    (ms: number) => {
      clearTimer()
      startRef.current = Date.now()
      timerRef.current = window.setTimeout(() => onDismiss(item.id), ms)
    },
    [clearTimer, item.id, onDismiss],
  )

  useEffect(() => {
    const raf = window.requestAnimationFrame(() => setEntered(true))
    schedule(item.duration)
    return () => {
      window.cancelAnimationFrame(raf)
      clearTimer()
    }
  }, [schedule, clearTimer, item.duration])

  const handleMouseEnter = () => {
    if (timerRef.current === null) return
    const elapsed = Date.now() - startRef.current
    remainingRef.current = Math.max(200, remainingRef.current - elapsed)
    clearTimer()
  }

  const handleMouseLeave = () => {
    schedule(remainingRef.current)
  }

  const classes = [
    'toast',
    `toast-${item.variant}`,
    entered ? 'toast-enter' : '',
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <div
      className={classes}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onFocus={handleMouseEnter}
      onBlur={handleMouseLeave}
    >
      <span className="toast-icon" aria-hidden="true">
        {TOAST_ICON[item.variant]}
      </span>
      <p className="toast-message">{item.message}</p>
      <button
        type="button"
        className="toast-close"
        aria-label="Fechar notificação"
        onClick={() => onDismiss(item.id)}
      >
        <span aria-hidden="true">×</span>
      </button>
    </div>
  )
}
