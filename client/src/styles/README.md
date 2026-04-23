# Design Tokens

Tokens CSS centralizam **cores, tipografia, espaçamento, raios, sombras e motion**. Todos os componentes/páginas devem consumir `var(--token)` — nada hard-coded em `index.css` nem em estilos por página.

Arquivo único: `client/src/styles/tokens.css`. Importado **antes** de `index.css` em `client/src/main.tsx`.

## Direção visual

**Emerald + Tangerine sobre Slate frio.**

- **Verde-esmeralda** (`--brand-*`) transmite GO/forward/saúde. Cor primária de CTAs, links ativos e gauge ideal.
- **Laranja-tangerina** (`--accent-*`) é energia/ritmo. Substitui o roxo `#aa3bff` da iteração anterior.
- **Slate frio** para neutros (substitui preto puro). O "preto" do dark é `#0F172A` (slate-900), nunca `#000`.

Light é o tema primário; dark é opt-in via `@media (prefers-color-scheme: dark)`.

## Paleta (PRD seção 18.2)

### Brand

| Token         | Hex       | Uso                                      |
|---------------|-----------|------------------------------------------|
| `--brand-50`  | `#ECFDF5` | Background de banner suave de sucesso    |
| `--brand-100` | `#D1FAE5` | Hover sutil em chips/badges, gauge ideal |
| `--brand-500` | `#10B981` | **Cor primária** — CTA, links ativos     |
| `--brand-600` | `#059669` | Hover/focus do CTA                       |
| `--brand-700` | `#047857` | Pressed/active do CTA                    |

### Accent

| Token          | Hex       | Uso                                  |
|----------------|-----------|--------------------------------------|
| `--accent-50`  | `#FFF7ED` | Background suave do accent           |
| `--accent-400` | `#FB923C` | Highlight de energia, botão secundário |
| `--accent-500` | `#F97316` | Hover do accent                      |

### Neutros (Slate frio)

| Token              | Hex       | Uso                                     |
|--------------------|-----------|-----------------------------------------|
| `--bg`             | `#F8FAFC` | Fundo da app (light)                    |
| `--surface`        | `#FFFFFF` | Cards, modais, inputs                   |
| `--surface-raised` | `#FFFFFF` | Cards elevados, dropdowns (+shadow-md)  |
| `--surface-muted`  | `#F1F5F9` | Tracks de barra, code background, fills |
| `--border`         | `#E2E8F0` | Bordas padrão                           |
| `--border-strong`  | `#CBD5E1` | Bordas hover/focus                      |
| `--text`           | `#0F172A` | Texto headline (NÃO usar `#000`)        |
| `--text-muted`     | `#475569` | Texto corrente (parágrafos, labels)     |
| `--text-subtle`    | `#94A3B8` | Texto secundário (hints, captions)      |
| `--text-on-brand`  | `#FFFFFF` | Texto sobre fundo `--brand-500`         |

### Semânticas

| Token       | Hex       | Uso                                    |
|-------------|-----------|----------------------------------------|
| `--success` | `#10B981` | = `--brand-500` (verde)                |
| `--warning` | `#F59E0B` | Banners de atenção, FPS marginal       |
| `--danger`  | `#EF4444` | Erros de validação, recomendações críticas |
| `--info`    | `#0EA5E9` | Banners informativos, dicas            |

Variantes auxiliares: `--warning-soft` / `--warning-text`, `--danger-soft` / `--danger-text` para banners suaves.

### Severidades de recomendação

| Severidade   | `--severity-*-bg` | `--severity-*-border` | `--severity-*-text` |
|--------------|-------------------|-----------------------|---------------------|
| Crítico      | `#FEF2F2`         | `#DC2626`             | `#7F1D1D`           |
| Atenção      | `#FFFBEB`         | `#D97706`             | `#78350F`           |
| Informativo  | `#F0FDF4`         | `#059669`             | `#064E3B`           |

### Tema escuro (opt-in)

Slate profundo, brand/accent mais claros para contraste. **Nunca preto puro.**

| Token                 | Hex (dark) |
|-----------------------|------------|
| `--bg`                | `#0F172A` (slate-900) |
| `--surface`           | `#1E293B` (slate-800) |
| `--border`            | `#334155` (slate-700) |
| `--text`              | `#F8FAFC`  |
| `--text-muted`        | `#CBD5E1`  |
| `--brand-500` (dark)  | `#34D399` (mais claro p/ contraste) |
| `--accent-400` (dark) | `#FDBA74`  |

## Tipografia (PRD 18.3)

| Token            | Família                                                | Pesos        |
|------------------|--------------------------------------------------------|--------------|
| `--font-display` | `'Space Grotesk', system-ui, sans-serif`               | 500/600/700  |
| `--font-body`    | `'Inter', system-ui, sans-serif`                       | 400/500/600  |
| `--font-mono`    | `ui-monospace, 'JetBrains Mono', Consolas, monospace`  | 400/500      |

Escala (mobile/desktop iguais salvo `--text-xl` / `--text-2xl` / `--text-3xl` / `--text-display`):

| Token            | Mobile | Desktop |
|------------------|--------|---------|
| `--text-xs`      | 12     | 12      |
| `--text-sm`      | 14     | 14      |
| `--text-base`    | 16     | 16      |
| `--text-lg`      | 18     | 18      |
| `--text-xl`      | 20     | 22      |
| `--text-2xl`     | 24     | 28      |
| `--text-3xl`     | 28     | 36      |
| `--text-display` | 40     | 56      |

> **Nota:** `--text-base = 16px` previne zoom no iOS quando o usuário foca um input.
> Sempre aplicar `font-variant-numeric: tabular-nums` em números (notas, paces, ângulos, contadores).

`--leading-tight: 1.2` para display/headlines; `--leading-normal: 1.5` para corpo.

Fontes carregadas via Google Fonts com `<link rel="preload" as="font" crossorigin>` + `<link rel="stylesheet" ... display=swap>` em `client/index.html`.

## Espaçamento (PRD 18.4)

Escala 4px:

```
--space-1 = 4px    --space-8  = 32px
--space-2 = 8px    --space-10 = 40px
--space-3 = 12px   --space-12 = 48px
--space-4 = 16px   --space-16 = 64px
--space-5 = 20px   --space-20 = 80px
--space-6 = 24px   --space-24 = 96px
```

## Raios (PRD 18.4) — concêntricos, child ≤ parent

```
--radius-xs   = 4px       --radius-lg   = 14px
--radius-sm   = 6px       --radius-xl   = 20px
--radius-md   = 10px      --radius-2xl  = 28px
--radius-full = 9999px
```

## Sombras (PRD 18.4) — ambient + direct, 2 camadas

```
--shadow-xs    = 0 1px 2px rgba(15,23,42,0.04)
--shadow-sm    = 0 1px 3px rgba(15,23,42,0.08), 0 1px 2px rgba(15,23,42,0.04)
--shadow-md    = 0 4px 8px rgba(15,23,42,0.06), 0 2px 4px rgba(15,23,42,0.04)
--shadow-lg    = 0 12px 24px rgba(15,23,42,0.10), 0 4px 8px rgba(15,23,42,0.06)
--shadow-focus = 0 0 0 3px rgba(16,185,129,0.35)   /* anel verde-emerald */
```

## Motion (PRD 18.4)

```
--duration-fast = 120ms   /* hover de botões, mudança de cor */
--duration-base = 200ms   /* transições padrão */
--duration-slow = 320ms   /* entrada de cards, mudança de página */

--ease-standard = cubic-bezier(0.4, 0, 0.2, 1)
--ease-out      = cubic-bezier(0.16, 1, 0.3, 1)   /* entradas */
--ease-in       = cubic-bezier(0.4, 0, 1, 1)      /* saídas */
```

**Regras (PRD 18.4):**
- Sempre animar **somente** `transform` e `opacity` (compositor-friendly).
- Nunca `width/height/top/left`.
- Listar propriedades explicitamente — proibido `transition: all`.
- Honrar `prefers-reduced-motion: reduce` removendo todas as animações decorativas (a aplicar em US-030).
