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
