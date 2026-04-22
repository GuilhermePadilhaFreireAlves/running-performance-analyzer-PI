# Frontend (client/) — notas para iterações futuras

## Stack
Vite 8 + React 19 + TypeScript 6 (scaffolding `create-vite --template react-ts`). Dependências runtime: `react`, `react-dom`, `react-router-dom`, `axios`.

## Comandos
Sempre executar a partir de `client/`:
- `npm install` — instala dependências (não é necessário re-instalar entre iterações).
- `npm run dev` — Vite dev server em `http://localhost:5173`.
- `npm run build` — roda `tsc -b` + `vite build`. **Esse é o typecheck da história** (equivalente ao `mypy` do backend).
- `npm run lint` — ESLint (opcional; não é bloqueador das histórias).
- `npm test` — Vitest (executa `vitest run` em ambiente Node, sem JSDOM). Use para testes de utilitários puros em `src/utils/*.test.ts`.

`tsconfig.app.json` tem `verbatimModuleSyntax: true` → sempre importe tipos com `import type { ... }`. Tem também `erasableSyntaxOnly: true` → não use `enum`/`namespace` (use objetos `as const`).

## Estrutura
```
client/src/
  api/
    client.ts      # axios instance, VITE_API_BASE_URL, interceptor de token
    auth.ts        # loginRequest, signupRequest, tipos LoginPayload/SignupPayload/UserProfile
  context/
    AuthContext.tsx  # AuthProvider + useAuth() hook; persiste token em localStorage
  components/
    PrivateRoute.tsx # redireciona para /login quando !isAuthenticated
  pages/<Tela>Page.tsx
  App.tsx          # BrowserRouter + rotas; envolve tudo em AuthProvider
  main.tsx         # entrypoint Vite
```

Adicione novas páginas em `src/pages/<Nome>Page.tsx`, novas chamadas de API em `src/api/<recurso>.ts`, novos hooks em `src/hooks/` (criar ao precisar). Utilitários puros (testáveis sem DOM) ficam em `src/utils/<nome>.ts` e os testes ao lado em `src/utils/<nome>.test.ts` (Vitest, ambiente Node — não usa JSDOM).

## Convenções (já instaladas)
- **Base URL**: `API_BASE_URL` em `src/api/client.ts` lê `import.meta.env.VITE_API_BASE_URL` com fallback `http://localhost:8000`. Override via `.env.local` em `client/` (veja `.env.example`).
- **Token**: chave `TOKEN_STORAGE_KEY = 'running_analyzer_token'` em localStorage. O interceptor do axios anexa `Authorization: Bearer <token>` automaticamente em toda requisição — **não** adicione headers manualmente nas chamadas.
- **Auth**: `useAuth()` expõe `{ user, token, isAuthenticated, login, signup, logout }`. `login({email, senha})` e `signup(payload)` já atualizam o estado + localStorage; `signup` faz login automático em seguida. Decodificação do JWT é manual (função `decodeTokenSubject`) — não dependemos de lib externa.
- **Rota privada**: envolva o elemento da rota em `<PrivateRoute>` para redirecionar a `/login` quando não autenticado. `login` persiste o `location.pathname` em `state.from` para futuro retorno (US-021 pode consumir).
- **Rotas esperadas** (já criadas como placeholder): `/login`, `/signup`, `/upload`, `/status/:id`, `/analysis/:id`, `/analysis/:id/raw`, `/historico`. Path de fallback (`*`) redireciona para `/login`.
- **Erros de API**: use o helper `extractApiError(err)` em `src/api/errors.ts` para converter rejeições do axios em `{ general: string | null, fields: Record<string, string> }`. Cobre 401, 409, 422 (lista FastAPI de `{loc, msg}` → map por campo) e erros de rede. Padrão de uso: `try { await chamada() } catch (err) { const { general, fields } = extractApiError(err); ... }`.
- **Estilo de formulário**: classes CSS compartilhadas em `src/index.css` — `auth-container`, `auth-form`, `.field` (wrapper de label/input), `.field-error` (erro de campo), `.form-error` (erro geral). Reutilize em qualquer formulário novo (upload, etc.). Use `<form noValidate>` para que a validação React dite a UX em vez de tooltips nativos.
- **Guard "já autenticado"** em páginas de auth: no corpo do componente, `if (isAuthenticated) return <Navigate to={redirectTo} replace />`. Nada de `useEffect + navigate()` (causa flash de conteúdo). Mesmo padrão do `PrivateRoute`.

## Contratos com o backend
- `POST /api/auth/login` → `{ access_token, token_type }` (JWT HS256, TTL 60 min).
- `POST /api/users/register` → `UserProfile` (sem senha). Hook `signup` faz register + login em sequência.
- Demais endpoints consumidos por histórias futuras: `POST /api/videos/upload`, `GET /api/videos/{id}/status`, `GET /api/analysis/{id}/simple`, `GET /api/analysis/{id}/raw`, `GET /api/historico-analise?page=&limit=`.
