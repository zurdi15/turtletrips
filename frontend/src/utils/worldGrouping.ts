import type { WorldPlace, WorldPlaceKind } from '../api/types'
import { COUNTRIES, countryName, flagEmoji } from '../countries'
import { intlLocale } from '../i18n'

export const KIND_KEYS: Record<WorldPlaceKind, string> = {
  country: 'world.kind.country',
  region: 'world.kind.region',
  city: 'world.kind.city',
  place: 'world.kind.place',
}

export { KIND_COLORS } from '../theme'

/** Los países auto guardan el código ISO como nombre; se muestra traducido. */
export function displayName(place: WorldPlace): string {
  if (place.kind === 'country' && place.country_code) return countryName(place.country_code)
  return place.name
}

/** "may 2018" o "2018" según haya mes; null sin fecha de visita */
export function visitedLabel(place: WorldPlace): string | null {
  if (place.visited_year == null) return null
  if (place.visited_month == null) return String(place.visited_year)
  const month = new Date(place.visited_year, place.visited_month - 1, 1).toLocaleDateString(
    intlLocale(),
    { month: 'short' },
  )
  return `${month} ${place.visited_year}`
}

/** Filtros del diario: multiselección, con lista vacía = sin filtrar. */
export interface WorldFilterState {
  searchText: string
  kinds: WorldPlaceKind[]
  sources: ('auto' | 'manual')[]
  countries: string[] // códigos ISO
  years: number[] // años de visita
}

export function emptyWorldFilters(): WorldFilterState {
  return { searchText: '', kinds: [], sources: [], countries: [], years: [] }
}

export function countWorldFilters(f: WorldFilterState): number {
  return (
    (f.searchText.trim() ? 1 : 0) +
    (f.kinds.length ? 1 : 0) +
    (f.sources.length ? 1 : 0) +
    (f.countries.length ? 1 : 0) +
    (f.years.length ? 1 : 0)
  )
}

export function filterWorldPlaces(items: WorldPlace[], f: WorldFilterState): WorldPlace[] {
  return items.filter((p) => {
    if (f.kinds.length && !f.kinds.includes(p.kind)) return false
    if (f.sources.length && !f.sources.includes(p.auto ? 'auto' : 'manual')) return false
    if (f.countries.length && !(p.country_code && f.countries.includes(p.country_code)))
      return false
    if (f.years.length && !(p.visited_year != null && f.years.includes(p.visited_year)))
      return false
    if (f.searchText) {
      const q = f.searchText.toLowerCase()
      if (
        !displayName(p).toLowerCase().includes(q) &&
        !(p.note ?? '').toLowerCase().includes(q) &&
        !(p.origin ?? '').toLowerCase().includes(q)
      )
        return false
    }
    return true
  })
}

export interface CountryGroup {
  code: string | null
  /** null = sin país asignado; el componente lo traduce (world.noCountry) */
  title: string | null
  flag: string
  entry: WorldPlace | null
  children: WorldPlace[]
}

/** Agrupa por país: la entrada 'country' preside y ciudades/sitios cuelgan; "Sin país" al final. */
export function groupByCountry(filtered: WorldPlace[]): CountryGroup[] {
  const byCode = new Map<string, CountryGroup>()
  const ensure = (code: string | null): CountryGroup => {
    const key = code ?? '__none__'
    let group = byCode.get(key)
    if (!group) {
      group = {
        code,
        title: code ? countryName(code) : null,
        flag: code ? flagEmoji(code) : '🌐',
        entry: null,
        children: [],
      }
      byCode.set(key, group)
    }
    return group
  }
  for (const place of filtered) {
    if (place.kind === 'country') ensure(place.country_code).entry = place
    else ensure(place.country_code).children.push(place)
  }
  const kindOrder: Record<string, number> = { region: 0, city: 1, place: 2 }
  for (const group of byCode.values()) {
    group.children.sort(
      (a, b) =>
        (kindOrder[a.kind] ?? 2) - (kindOrder[b.kind] ?? 2) ||
        a.name.localeCompare(b.name, 'es'),
    )
  }
  return [...byCode.values()].sort((a, b) => {
    if (a.code === null) return 1
    if (b.code === null) return -1
    return (a.title ?? '').localeCompare(b.title ?? '', 'es')
  })
}

export interface TimelineYear {
  year: number
  entries: WorldPlace[]
}

/**
 * Historia viajera: entradas del diario con fecha agrupadas por año (ascendente,
 * la historia se lee desde el principio). Dentro del año: por mes (sin mes al
 * final), países antes que ciudades/sitios, y alfabético de desempate.
 */
export function buildTimeline(items: WorldPlace[]): TimelineYear[] {
  const kindOrder: Record<string, number> = { country: 0, region: 1, city: 2, place: 3 }
  const byYear = new Map<number, WorldPlace[]>()
  for (const place of items) {
    if (place.visited_year == null) continue
    byYear.set(place.visited_year, [...(byYear.get(place.visited_year) ?? []), place])
  }
  return [...byYear.entries()]
    .sort((a, b) => a[0] - b[0])
    .map(([year, entries]) => ({
      year,
      entries: entries.sort(
        (a, b) =>
          (a.visited_month ?? 13) - (b.visited_month ?? 13) ||
          (kindOrder[a.kind] ?? 3) - (kindOrder[b.kind] ?? 3) ||
          displayName(a).localeCompare(displayName(b), 'es'),
      ),
    }))
}

/**
 * Reordena los grupos de país por fecha de visita del país (los que no la
 * tienen quedan al final conservando el alfabético de groupByCountry, porque
 * Array.sort es estable).
 */
export function sortCountryGroups(groups: CountryGroup[], desc: boolean): CountryGroup[] {
  const stamp = (group: CountryGroup): number | null => {
    const year = group.entry?.visited_year
    if (year == null) return null
    return year * 100 + (group.entry?.visited_month ?? 0)
  }
  return [...groups].sort((a, b) => {
    const sa = stamp(a)
    const sb = stamp(b)
    if (sa == null && sb == null) return 0
    if (sa == null) return 1
    if (sb == null) return -1
    return desc ? sb - sa : sa - sb
  })
}

// la cronología con filtros: años visibles y "huecos" donde los filtros
// ocultan entradas (años enteros consecutivos se funden en un solo hueco)
export type TimelineSegment =
  | { type: 'year'; year: number; entries: WorldPlace[]; hidden: number }
  | { type: 'gap'; hidden: number }

export function buildTimelineSegments(
  all: WorldPlace[],
  visible: WorldPlace[],
): TimelineSegment[] {
  const visibleIds = new Set(visible.map((p) => p.id))
  const segments: TimelineSegment[] = []
  for (const yearGroup of buildTimeline(all)) {
    const entries = yearGroup.entries.filter((e) => visibleIds.has(e.id))
    const hidden = yearGroup.entries.length - entries.length
    if (!entries.length) {
      const last = segments[segments.length - 1]
      if (last?.type === 'gap') last.hidden += hidden
      else segments.push({ type: 'gap', hidden })
    } else {
      segments.push({ type: 'year', year: yearGroup.year, entries, hidden })
    }
  }
  return segments
}

export interface WorldStats {
  countries: number
  worldPct: number
  regions: number
  cities: number
  places: number
}

export function worldStats(items: WorldPlace[], totalCountries = COUNTRIES.length): WorldStats {
  const countries = items.filter((p) => p.kind === 'country').length
  return {
    countries,
    worldPct: Math.round((countries / totalCountries) * 100),
    regions: items.filter((p) => p.kind === 'region').length,
    cities: items.filter((p) => p.kind === 'city').length,
    places: items.filter((p) => p.kind === 'place').length,
  }
}

/** Deduce el país a partir del display_name de Nominatim ("…, España" o "…, Spain"). */
export function inferCountryCode(displayNameResult: string): string | null {
  const last = displayNameResult.split(',').pop()?.trim().toLowerCase()
  if (!last) return null
  return (
    COUNTRIES.find((c) => c.es.toLowerCase() === last || c.en.toLowerCase() === last)?.code ?? null
  )
}
