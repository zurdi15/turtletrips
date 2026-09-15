import type { LinkGroup, TripLink, TripLinkBucket } from '../api/types'

/** Clave del cubo "sin bloque" en los espejos locales del drag & drop. */
export const NO_GROUP_KEY = 'none'

export function bucketKey(groupId: number | null): string {
  return groupId === null ? NO_GROUP_KEY : String(groupId)
}

export interface LinkSection {
  /** null = enlaces sin bloque */
  group: LinkGroup | null
  links: TripLink[]
}

function byPosition<T extends { position: number; id: number }>(a: T, b: T): number {
  return a.position - b.position || a.id - b.id
}

/**
 * Agrupa los enlaces por bloque, en el orden manual de los bloques, y deja
 * los que no tienen bloque al final. Un enlace cuyo bloque ya no existe
 * (respuesta desfasada) cae también en "sin bloque".
 */
export function groupLinks(groups: LinkGroup[], links: TripLink[]): LinkSection[] {
  const ordered = groups.slice().sort(byPosition)
  const known = new Set(ordered.map((g) => g.id))
  const byGroup = new Map<number | null, TripLink[]>()
  for (const link of links.slice().sort(byPosition)) {
    const key = link.group_id !== null && known.has(link.group_id) ? link.group_id : null
    const list = byGroup.get(key)
    if (list) list.push(link)
    else byGroup.set(key, [link])
  }
  const sections: LinkSection[] = ordered.map((group) => ({
    group,
    links: byGroup.get(group.id) ?? [],
  }))
  sections.push({ group: null, links: byGroup.get(null) ?? [] })
  return sections
}

/**
 * Traduce los espejos locales (clave de cubo → enlaces en orden) al payload
 * del endpoint de reorder.
 */
export function bucketsFromLists(lists: Record<string, TripLink[]>): TripLinkBucket[] {
  return Object.entries(lists).map(([key, links]) => ({
    group_id: key === NO_GROUP_KEY ? null : Number(key),
    ids: links.map((link) => link.id),
  }))
}

/** Dominio legible de un enlace ("booking.com"), o la URL tal cual si no parsea. */
export function linkHost(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, '')
  } catch {
    return url
  }
}
