/**
 * Identidade da marca consumida pela UI (top nav, <title>, favicon, etc.).
 * Mantenha aqui a única fonte da verdade — não duplique strings em componentes.
 */
export const BRAND_NAME = 'Stride'
export const BRAND_TAGLINE = 'Análise biomecânica de corrida'

/** Helper utilizado por hooks de título de página: 'Tela — Stride'. */
export function pageTitle(label: string): string {
  return `${label} — ${BRAND_NAME}`
}
