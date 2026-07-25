import type { WorldPlace, WorldPlaceKind } from '../api/types'
import { COUNTRIES, countryName, flagEmoji } from '../countries'

export const KIND_LABELS: Record<WorldPlaceKind, string> = {
  country: 'País',
  city: 'Ciudad',
  place: 'Sitio',
}

export { KIND_COLORS } from '../theme'

/** Los países auto guardan el código ISO como nombre; se muestra traducido. */
export function displayName(place: WorldPlace): string {
  if (place.kind === 'country' && place.country_code) return countryName(place.country_code)
  return place.name
}

export interface WorldFilterState {
  searchText: string
  kind: 'all' | WorldPlaceKind
  source: 'all' | 'auto' | 'manual'
  country: string // 'all' o código ISO
}

export function emptyWorldFilters(): WorldFilterState {
  return { searchText: '', kind: 'all', source: 'all', country: 'all' }
}

export function filterWorldPlaces(items: WorldPlace[], f: WorldFilterState): WorldPlace[] {
  return items.filter((p) => {
    if (f.kind !== 'all' && p.kind !== f.kind) return false
    if (f.source === 'auto' && !p.auto) return false
    if (f.source === 'manual' && p.auto) return false
    if (f.country !== 'all' && p.country_code !== f.country) return false
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
  title: string
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
        title: code ? countryName(code) : 'Sin país asignado',
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
    return a.title.localeCompare(b.title, 'es')
  })
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

/** Deduce el país a partir del display_name de Nominatim ("…, España"). */
export function inferCountryCode(displayNameResult: string): string | null {
  const last = displayNameResult.split(',').pop()?.trim().toLowerCase()
  if (!last) return null
  return COUNTRIES.find((c) => c.es.toLowerCase() === last)?.code ?? null
}
