# Frontend (client/) — notas para iterações futuras

## Stack
Vite 8 + React 19 + TypeScript 6 (scaffolding `create-vite --template react-ts`). Dependências runtime: `react`, `react-dom`, `react-router-dom`, `axios`, `recharts` (apenas usado em `AnalysisRawPage` para séries por frame — considere dynamic import se precisar reduzir bundle em histórias futuras).

## Paleta de charts (US-040)
Para quaisquer gráficos/overlays que codifiquem esq vs dir ou múltiplas séries numéricas, consuma `OKABE_ITO` em `client/src/utils/rawAnalysis.ts` (`bluishGreen`=esq, `vermillion`=dir, `blue`=tronco, `reddishPurple`=Y CoM, `orange/skyBlue/yellow` disponíveis). Paleta Okabe-Ito preserva contraste em daltonismo e escala de cinza. Faixas ideais por métrica (joelho 15–25°, cotovelo 70–110°, tronco 4–8°) vivem em `FAIXAS_IDEAIS` e replicam `server/src/biomechanics/recomendacoes.py#_classificar_*` — sincronize manualmente se o backend mudar os limiares.

## Sparkline e filtros deep-linkados (US-041)
Para mini-charts de baixa cardinalidade (evolução de uma única série numérica), use `<Sparkline>` em `client/src/components/historico/Sparkline.tsx` — SVG inline puro (sem Recharts), escala fixa configurável. Mantém o bundle leve em páginas que não precisam de Recharts inteiro. Recebe `SparklinePoint[]` (de `historicoDisplay.ts#sparklinePoints`) já ordenado cronologicamente ascendente.

Filtros via query string (URL canônica + deep-link): cada filtro tem `parse<Filtro>Param` puro em `historicoDisplay.ts` (default → `null` no parser). Convenção de URL: **omitir** o param quando o valor é o default (em vez de `set('chave', 'todos')`); trocar de filtro **sempre** zera `page` (deletar `page` em vez de setar 1). Resultado: URL canônica curta, back/forward no browser navega entre estados consistentes.

Restauração de scroll back/forward em listagens master/detalhe: `sessionStorage['<lista>:scroll']` como bridge — salva `window.scrollY` antes de `navigate(detalhe)`, restaura no `useEffect` de fetch após `loading=false` (usar `useRef(false)` para garantir restore só na primeira hidratação). Funciona com `BrowserRouter` sem precisar de `<ScrollRestoration>` (data routers).

Datas em pt-BR: `Intl.DateTimeFormat('pt-BR', {dateStyle, timeStyle})` adiciona vírgula entre data e hora em alguns engines. Para shape estável `dd/mm/yyyy HH:MM`, declare dois formatters (apenas date / apenas time) no module-level e concatene com espaço.

## App Shell e marca (US-029)
Nome da marca em `client/src/branding.ts` (`BRAND_NAME = 'Stride'` + helper `pageTitle(label)` → `'Label — Stride'`). Toda string de marca/título consome esse módulo — não duplique. O `<AppShell>` em `client/src/components/AppShell.tsx` envolve **todas** as rotas privadas (Login/Signup ficam fora) e renderiza: top nav `position: sticky; top: 0` (height 64px) com logo+nav desktop visível em ≥640px e hamburger drawer em <640px → `<div className="app-shell-main">` (contém o `<main>` da página) → footer mínimo. O `AppShell` **não** renderiza `<main>` — cada página é dona do seu `<main id="main" tabIndex={-1}>` (ver seção Acessibilidade base). O drawer mobile aplica `inert` em `#shell-root` enquanto aberto e devolve foco ao botão hamburger no fechamento; backdrop fecha por clique e Escape no teclado fecha drawer e user-menu. Em `App.tsx`, use o helper `privateElement(<Page/>)` em vez de aninhar `<PrivateRoute><AppShell>...</AppShell></PrivateRoute>` manualmente. Ícones/símbolos da marca: `Logo` em `client/src/components/Logo.tsx` (SVG inline com `currentColor`) — favicon SVG em `client/public/favicon.svg` reproduz o mesmo símbolo sobre fundo verde brand. `client/index.html` tem `lang="pt-BR"` e `<title>Stride</title>` (placeholder para SSR; cada página sobrescreve via hook). Cada página privada/auth declara seu título com `usePageTitle('Tela')` em `client/src/hooks/usePageTitle.ts` — o hook restaura o título anterior no unmount.

## Acessibilidade base (US-030)
Skip-to-content (`<a className="skip-link" href="#main">`) vive em `client/src/App.tsx` **fora** de `<Routes>` — primeiro elemento focável em qualquer rota (incluindo Login/Signup). Toda página (privada ou auth) é dona do seu próprio `<main id="main" tabIndex={-1} className="...">` como raiz do JSX — nunca mais de um `<main>` por página, nunca `<main>` aninhado dentro do `AppShell`. `tabIndex={-1}` permite o skip-link mover foco para o container sem colocá-lo no tab-order natural. Estilos globais de a11y em `client/src/index.css`:
- `*:focus-visible { outline: none; box-shadow: var(--shadow-focus) }` — anel verde consistente em todo interativo. Nunca use `outline: none` sem replacement visível.
- `@media (prefers-reduced-motion: reduce)` neutraliza `transition-duration`, `animation-duration`, `animation-iteration-count` e `scroll-behavior` em `*`, `*::before`, `*::after`.
- `h1..h6 { scroll-margin-top: var(--space-16) }` compensa a top nav `sticky` ao rolar até âncoras.
- `main[tabindex]:focus { outline: none }` — o `:focus-visible` fica com `*:focus-visible`; `:focus` mouse/programático no main não renderiza outline visível porque o usuário acabou de clicar num skip-link e não precisa ver o container piscando.

Hierarquia de heading: exatamente **um `<h1>` por página**, `<h2>` para seções. Botões icon-only (hamburger, drawer close, user-menu, paginação do histórico) precisam de `aria-label` descritivo em pt-BR; decorações em texto (setas `←`/`→`) ficam `aria-hidden="true"` para não serem lidas pelo leitor de tela.

## Biblioteca de componentes (US-031, US-033)
Componentes React compartilhados vivem em `client/src/components/ui/` (`Button`, `Input`, `Field`, `Card`, `Badge`, `Banner`, `Skeleton`) e subpacote `states/` (`LoadingState`, `EmptyState`, `ErrorState` — US-033). Todos são reexportados via o barrel `index.ts`. Importe sempre pelo barrel:

```tsx
import { Button, Field, Card, Badge, Banner, Skeleton } from '../components/ui'
import { LoadingState, EmptyState, ErrorState } from '../components/ui'
import type { ButtonProps } from '../components/ui'
```

Princípios:
- Estilos são classes `.ui-*` globais em `client/src/index.css` consumindo exclusivamente tokens — nada de CSS Modules/styled-components.
- Props tipadas com `import type`; componentes que precisam de spread nativo (Button, Input) estendem `HTMLAttributes<Element>`.
- `Button` com `loading=true` mostra spinner **sem apagar o label original** (UX deliberada); define `aria-busy` + `disabled` enquanto loading.
- `Input` aplica `font-size: 16px` no mobile para evitar o auto-zoom do iOS; em viewports ≥640px cai para `--text-sm`.
- `Field` usa `useId()` como fallback para o `id` e liga `aria-describedby` à mensagem de erro/hint ativa. `error` precede `hint`.
- `Banner` troca `role="status"` (polite, default) por `role="alert"` (assertive) via prop `assertive` — reserve assertive para erros que precisam interromper.
- `Skeleton` aceita qualquer CSS em `width`/`height` e um flag `rounded` para círculos (avatar). Use para espelhar o layout final e prevenir CLS.
- `LoadingState variant="status|analysis|analysis-raw|historico"` — compõe Skeletons com dimensões fixas espelhando o layout final de cada página. Container externo tem `role="status"`, `aria-busy="true"`, `aria-live="polite"` + label visualmente oculta (classe utilitária `.visually-hidden` em `index.css`). Para novas páginas no redesign, adicione uma nova `LoadingVariant` em `components/ui/states/LoadingState.tsx` com as mesmas dimensões do layout real — não reutilize uma variante existente se o layout diverge.
- `ErrorState` exige pelo menos uma próxima ação: `onRetry?: () => void`, `backTo?: {to, label}` ou `action?: ReactNode`. "No dead ends" é regra dura — nunca renderize `ErrorState` sem próxima ação. Para retry na mesma rota, o padrão é um `retryCount` state incrementado pelo `onRetry` e colocado na dep array do `useEffect` de fetch.
- `EmptyState` exige CTA via prop `action` (`ReactNode` — geralmente um `<Button>`). SVG ilustração default é decorativo (`aria-hidden`); customize com a prop `illustration` se a tela pedir arte específica.

**US-031 criou a biblioteca e US-033 padronizou os estados de carregamento/vazio/erro — as 4 páginas principais (Status, Analysis, AnalysisRaw, Histórico) já consomem `LoadingState`/`ErrorState`/`EmptyState`. Histórias de redesign (US-035+) migram o restante do layout para `Button`/`Field`/`Card`/etc.**

## Responsividade mobile-first (US-034)
- `#root` é o contêiner global: `max-width: 1280px; margin-inline: auto; padding-inline` escalando de `var(--space-4)` (<640px) → `var(--space-5)` (≥640px) → `var(--space-8)` (≥1024px). Não reintroduzir `width`/`border-inline` no `#root` — o chrome visual é responsabilidade da top nav + páginas.
- Breakpoints canônicos estão em `tokens.css`: `--bp-sm: 640px`, `--bp-md: 768px`, `--bp-lg: 1024px`, `--bp-xl: 1280px`. CSS não resolve `var()` em `@media`, então repita o literal (`@media (min-width: 640px)`) — o token serve de referência para quem lê.
- Safe areas: `.app-shell-header` aplica `padding-top/left/right: env(safe-area-inset-*)`. Qualquer nova barra fixa no topo (banner de sessão, wizard) deve fazer o mesmo, senão o notch do iPhone corta o conteúdo.
- Globals já instalados em `index.css`: `html { -webkit-tap-highlight-color: rgba(16,185,129,0.15) }`, `button/a/[role=button]/summary/label { touch-action: manipulation }`, `input/select/textarea { font-size: 16px }` (cai para `--text-sm` em ≥640px). Isso previne o auto-zoom do iOS e remove o delay de 300ms.
- Hit targets ≥ 44px no mobile — aplique `min-height: 44px` em qualquer novo controle interativo (inputs de formulário, botões de navegação/paginação). Padrão instalado para `.auth-form input/select`, `.historico-pagination-button`, `.historico-item-button`, `.ui-input`, `.ui-button-md` (via `@media max-width: 639px`), `.status-restart-button`, `.auth-form button[type=submit]`, `.analysis-primary-link`.
- Viewport meta (`client/index.html`): apenas `width=device-width, initial-scale=1.0`. **Nunca** adicione `user-scalable=no` ou `maximum-scale=1` — quebra acessibilidade e é proibido pela US-034/PRD.

## Design tokens (US-028)
Fonte única em `client/src/styles/tokens.css` (importado **antes** de `index.css` em `main.tsx`). Tema light + override completo via `@media (prefers-color-scheme: dark)`. Documentação tabular (paleta + escalas) em `client/src/styles/README.md`. Direção: **Emerald (`--brand-*`) + Tangerine (`--accent-*`) sobre Slate frio**; nunca preto puro (dark `--bg = #0F172A`). Convenção: `--text` = headline (`#0F172A`), `--text-muted` = body, `--text-subtle` = hints (invertido do esquema antigo `--text-h`/`--text`). Severidades de recomendação têm tokens dedicados `--severity-{critico,atencao,informativo}-{bg,border,text}` separados das semânticas genéricas (`--success/warning/danger/info`). Sempre consuma `var(--token)` em CSS — proibido hex/rgba hard-coded em `index.css` ou em estilos por página/componente.

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
- `POST /api/videos/upload` → `{ video_id, status }`. Multipart com `file` (UploadFile) + `pace_min_km` (form float). 422 cobre pace fora da faixa, FPS insuficiente e perspectiva não-lateral. Helper `uploadVideoRequest({file, paceMinKm})` em `src/api/videos.ts`.
- `GET /api/videos/{id}/status` → `{ video_id, status, status_descricao }`. Helper `getVideoStatusRequest(videoId)` em `src/api/videos.ts`. Status possíveis: `pendente`, `validando_perspectiva`, `detectando_pose`, `calculando_metricas`, `concluido`, `erro_qualidade_keypoints`, `erro_multiplas_pessoas`. Mapeamento para UI (estágios, progresso, mensagens de erro) vive em `src/utils/videoStatus.ts`.
- Demais endpoints consumidos por histórias futuras: `GET /api/analysis/{id}/simple`, `GET /api/analysis/{id}/raw`, `GET /api/historico-analise?page=&limit=`.

## Validação de vídeo no cliente (US-023)
- `src/utils/videoValidation.ts` exporta `validateVideoMetadata(meta)` (puro, testável em Node) com as constantes do PRD: `VIDEO_MIN_DURATION_SEC=30`, `VIDEO_MAX_DURATION_SEC=180`, `VIDEO_MIN_WIDTH=640`, `VIDEO_MIN_HEIGHT=480`, `VIDEO_MIN_FPS=60`. Mensagens em constantes (`VIDEO_TOO_SHORT_MESSAGE`, etc.) — qualquer tela futura que precise revalidar reusa daqui.
- `src/utils/videoMeta.ts#readVideoMetadata(file)` lê duração/largura/altura via `<video>` em memória + `URL.createObjectURL`, e tenta estimar FPS via `requestVideoFrameCallback` (best-effort). `estimatedFps` pode ser `null` quando o browser não suporta a API ou o autoplay falha — neste caso a validação não emite warning de FPS (backend ainda valida definitivamente). Sempre revogar o object URL e chamar `video.load()` no cleanup.
- `src/api/videos.ts#uploadVideoRequest({file, paceMinKm})` usa `FormData` (não JSON). O axios deixa o browser definir o `Content-Type: multipart/form-data; boundary=...` — não force header manual.

## Polling de status (US-024)
- `src/utils/videoStatus.ts` (puro, testado em Node) exporta: `STATUS_*` constants, `STATUS_STAGES` (lista de 4 etapas para UI), `stageIndexFromStatus`, `progressPercentFromStatus`, `isErrorStatus`, `errorMessageForStatus`, `isFinalStatus`. Mensagens de erro (`ERROR_KEYPOINTS_MESSAGE`, `ERROR_MULTIPLAS_PESSOAS_MESSAGE`) expandem as do backend em texto amigável.
- Padrão de polling em `pages/StatusPage.tsx`: `useEffect` inicia `poll()` que chama a API → `setState` → agenda próximo com `setTimeout(poll, 2000)` se não for estado final. Use `useRef<number | null>` para timer id e `useRef(false)` para flag de cancelamento. Na cleanup: marque `cancelledRef.current = true` + `clearTimeout`. Falhas transitórias continuam o polling (backend pode estar reiniciando); estado final (`concluido` ou erro) para e, em caso de `concluido`, navega para `/analysis/:id` com `replace: true`.
