import type { WorldPlace, WorldPlaceKind } from '../api/types'
import { COUNTRIES, countryName, flagEmoji } from '../countries'
import { intlLocale } from '../i18n'

export const KIND_KEYS: Record<WorldPlaceKind, string> = {
  country: 'world.kind.country',
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

export interface WorldFilterState {
  searchText: string
  kind: 'all' | WorldPlaceKind
  source: 'all' | 'auto' | 'manual'
  country: string // 'all' o código ISO
  year: 'all' | number // año de visita
}

export function emptyWorldFilters(): WorldFilterState {
  return { searchText: '', kind: 'all', source: 'all', country: 'all', year: 'all' }
}

export function filterWorldPlaces(items: WorldPlace[], f: WorldFilterState): WorldPlace[] {
  return items.filter((p) => {
    if (f.kind !== 'all' && p.kind !== f.kind) return false
    if (f.source === 'auto' && !p.auto) return false
    if (f.source === 'manual' && p.auto) return false
    if (f.country !== 'all' && p.country_code !== f.country) return false
    if (f.year !== 'all' && p.visited_year !== f.year) return false
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
  const kindOrder: Record<string, number> = { city: 0, place: 1 }
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
  const kindOrder: Record<string, number> = { country: 0, city: 1, place: 2 }
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

export interface WorldStats {
  countries: number
  worldPct: number
  cities: number
  places: number
}

export function worldStats(items: WorldPlace[], totalCountries = COUNTRIES.length): WorldStats {
  const countries = items.filter((p) => p.kind === 'country').length
  return {
    countries,
    worldPct: Math.round((countries / totalCountries) * 100),
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
