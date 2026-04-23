import { useCallback, useEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { BRAND_NAME } from '../branding'
import { Logo } from './Logo'

interface AppShellProps {
  children: ReactNode
}

interface NavItem {
  to: string
  label: string
}

const NAV_ITEMS: NavItem[] = [
  { to: '/upload', label: 'Análise' },
  { to: '/historico', label: 'Histórico' },
]

const MOBILE_BREAKPOINT_PX = 640

/** Iniciais do usuário (até 2 letras) — fallback para '?' quando ausente. */
function userInitials(name: string | undefined): string {
  if (!name) return '?'
  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (parts.length === 0) return '?'
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
}

/**
 * Shell persistente das rotas privadas: skip link, top nav fixa (logo + nav links
 * + menu de usuário), drawer mobile (<640px) com `inert` no body quando aberto,
 * e footer mínimo. Login/Signup ficam fora deste shell.
 */
export function AppShell({ children }: AppShellProps) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const userMenuRef = useRef<HTMLDivElement>(null)
  const drawerCloseBtnRef = useRef<HTMLButtonElement>(null)
  const hamburgerBtnRef = useRef<HTMLButtonElement>(null)

  const closeMenus = useCallback(() => {
    setUserMenuOpen(false)
    setDrawerOpen(false)
  }, [])

  useEffect(() => {
    closeMenus()
  }, [location.pathname, closeMenus])

  useEffect(() => {
    if (!userMenuOpen) return
    const handleClick = (event: MouseEvent) => {
      if (
        userMenuRef.current &&
        !userMenuRef.current.contains(event.target as Node)
      ) {
        setUserMenuOpen(false)
      }
    }
    const handleKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setUserMenuOpen(false)
    }
    document.addEventListener('mousedown', handleClick)
    document.addEventListener('keydown', handleKey)
    return () => {
      document.removeEventListener('mousedown', handleClick)
      document.removeEventListener('keydown', handleKey)
    }
  }, [userMenuOpen])

  // Drawer: aplicar `inert` no <main>+<footer> enquanto aberto e devolver foco
  // ao botão hamburger ao fechar (padrão de modal não-bloqueante).
  useEffect(() => {
    if (!drawerOpen) return
    const root = document.getElementById('shell-root')
    root?.setAttribute('inert', '')
    drawerCloseBtnRef.current?.focus()
    const handleKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setDrawerOpen(false)
    }
    document.addEventListener('keydown', handleKey)
    return () => {
      root?.removeAttribute('inert')
      document.removeEventListener('keydown', handleKey)
      hamburgerBtnRef.current?.focus()
    }
  }, [drawerOpen])

  // Em viewport >=640px o drawer não faz sentido; força fechado.
  useEffect(() => {
    const mql = window.matchMedia(`(min-width: ${MOBILE_BREAKPOINT_PX}px)`)
    const handle = (event: MediaQueryListEvent) => {
      if (event.matches) setDrawerOpen(false)
    }
    mql.addEventListener('change', handle)
    return () => mql.removeEventListener('change', handle)
  }, [])

  const handleLogout = () => {
    closeMenus()
    logout()
    navigate('/login', { replace: true })
  }

  const initials = userInitials(user?.name)
  const userLabel = user?.name ?? user?.email ?? 'Usuário'

  return (
    <>
      <a className="skip-link" href="#main">
        Pular para o conteúdo
      </a>

      <header className="app-shell-header" role="banner">
        <div className="app-shell-header-inner">
          <Link to="/upload" className="app-shell-brand" aria-label={`${BRAND_NAME} — início`}>
            <Logo size={28} />
            <span className="app-shell-brand-name">{BRAND_NAME}</span>
          </Link>

          <nav className="app-shell-nav" aria-label="Principal">
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `app-shell-nav-link${isActive ? ' app-shell-nav-link-active' : ''}`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>

          <div className="app-shell-user" ref={userMenuRef}>
            <button
              type="button"
              className="app-shell-user-button"
              onClick={() => setUserMenuOpen((open) => !open)}
              aria-haspopup="menu"
              aria-expanded={userMenuOpen}
              aria-label={`Menu do usuário ${userLabel}`}
            >
              <span className="app-shell-avatar" aria-hidden="true">
                {initials}
              </span>
            </button>
            {userMenuOpen ? (
              <div className="app-shell-user-menu" role="menu">
                <p className="app-shell-user-menu-name" role="presentation">
                  {userLabel}
                </p>
                <button
                  type="button"
                  className="app-shell-user-menu-item"
                  role="menuitem"
                  onClick={handleLogout}
                >
                  Sair
                </button>
              </div>
            ) : null}
          </div>

          <button
            type="button"
            ref={hamburgerBtnRef}
            className="app-shell-hamburger"
            onClick={() => setDrawerOpen(true)}
            aria-label="Abrir menu de navegação"
            aria-expanded={drawerOpen}
            aria-controls="app-shell-drawer"
          >
            <span className="app-shell-hamburger-bar" aria-hidden="true" />
            <span className="app-shell-hamburger-bar" aria-hidden="true" />
            <span className="app-shell-hamburger-bar" aria-hidden="true" />
          </button>
        </div>
      </header>

      {drawerOpen ? (
        <div
          className="app-shell-drawer-backdrop"
          onClick={() => setDrawerOpen(false)}
          aria-hidden="true"
        />
      ) : null}

      <aside
        id="app-shell-drawer"
        className={`app-shell-drawer${drawerOpen ? ' app-shell-drawer-open' : ''}`}
        aria-hidden={!drawerOpen}
        aria-label="Menu de navegação"
      >
        <div className="app-shell-drawer-header">
          <span className="app-shell-brand">
            <Logo size={24} />
            <span className="app-shell-brand-name">{BRAND_NAME}</span>
          </span>
          <button
            ref={drawerCloseBtnRef}
            type="button"
            className="app-shell-drawer-close"
            onClick={() => setDrawerOpen(false)}
            aria-label="Fechar menu"
          >
            ×
          </button>
        </div>
        <nav className="app-shell-drawer-nav" aria-label="Principal (mobile)">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `app-shell-drawer-link${isActive ? ' app-shell-drawer-link-active' : ''}`
              }
            >
              {item.label}
            </NavLink>
          ))}
          <button
            type="button"
            className="app-shell-drawer-link app-shell-drawer-logout"
            onClick={handleLogout}
          >
            Sair
          </button>
        </nav>
      </aside>

      <div id="shell-root" className="app-shell-root">
        <main id="main" className="app-shell-main" tabIndex={-1}>
          {children}
        </main>
        <footer className="app-shell-footer" role="contentinfo">
          <div className="app-shell-footer-inner">
            <span>
              {BRAND_NAME} · análise biomecânica de corrida
            </span>
            <Link to="/sobre" className="app-shell-footer-link">
              Sobre
            </Link>
          </div>
        </footer>
      </div>
    </>
  )
}
