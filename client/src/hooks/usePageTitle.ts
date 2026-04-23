import { useEffect } from 'react'
import { pageTitle } from '../branding'

/**
 * Atualiza `document.title` para 'label — Stride' enquanto o componente está
 * montado. Restaura o título anterior no unmount.
 */
export function usePageTitle(label: string): void {
  useEffect(() => {
    const previous = document.title
    document.title = pageTitle(label)
    return () => {
      document.title = previous
    }
  }, [label])
}
