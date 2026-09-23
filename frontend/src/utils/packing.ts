import type { PackingBucket } from '../api/types'

export interface PackingGroup<T> {
  name: string
  color: string | null
  items: T[]
}

/**
 * Agrupa elementos de maleta/plantilla por categoría: primero las categorías
 * conocidas (en su orden), después las huérfanas que solo existen en items
 * (categorías borradas de /settings). Los grupos vacíos se omiten.
 */
export function groupPackingItems<T extends { category: string }>(
  items: T[],
  knownCategories: string[],
  colorOf: (name: string) => string | null,
): PackingGroup<T>[] {
  const names = [
    ...knownCategories,
    ...new Set(items.map((i) => i.category).filter((c) => !knownCategories.includes(c))),
  ]
  return names
    .map((name) => ({
      name,
      color: colorOf(name),
      items: items.filter((i) => i.category === name),
    }))
    .filter((g) => g.items.length)
}

/**
 * Traduce los espejos locales del drag & drop (categoría → elementos en orden)
 * al payload del endpoint de reorder (vale para la maleta y para la plantilla,
 * que comparten forma). Las categorías vacías viajan igual: así un elemento
 * que salió de la última categoría deja su cubo a cero.
 */
export function packingBuckets(
  lists: Record<string, { id: number }[]>,
): PackingBucket[] {
  return Object.entries(lists).map(([category, items]) => ({
    category,
    ids: items.map((item) => item.id),
  }))
}
