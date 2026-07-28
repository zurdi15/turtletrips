// Estado de cada país en el mapa mundial: si está visitado y "cuánto" se ha
// visto de él, que es lo que gradúa la intensidad del relleno.
import type { WorldPlace } from '../api/types'

export type CountryStatus = 'none' | 'visited'

export interface CountryState {
  status: CountryStatus
  /** id de la entrada de país del diario (para editarla o quitarla) */
  placeId: number | null
  year: number | null
  /** ciudades y sitios del diario dentro del país */
  cities: number
  /** regiones (ISO 3166-2) marcadas dentro del país */
  regions: number
}

/** Estado por código ISO alpha-2 a partir del diario de la familia */
export function buildCountryStates(places: WorldPlace[]): Map<string, CountryState> {
  const states = new Map<string, CountryState>()

  function entry(code: string): CountryState {
    let state = states.get(code)
    if (!state) {
      state = { status: 'none', placeId: null, year: null, cities: 0, regions: 0 }
      states.set(code, state)
    }
    return state
  }

  for (const place of places) {
    const code = place.country_code
    if (!code) continue
    const state = entry(code)
    if (place.kind === 'country') {
      state.status = 'visited'
      state.placeId = place.id
      state.year = place.visited_year
    } else {
      if (place.kind === 'region') state.regions += 1
      else state.cities += 1
      // una región o ciudad sin país marcado también cuenta como país pisado: el
      // backend arrastra la entrada del país, pero el mapa no espera a recargar
      if (state.status === 'none') state.status = 'visited'
    }
  }

  return states
}

/**
 * Opacidad del relleno: arranca en un verde discreto al marcar el país y sube
 * con lo que hay apuntado dentro (regiones, ciudades y sitios), hasta un tope
 * legible. Deliberadamente BAJA: encima van los rótulos de la cartografía y el
 * mapa tiene que seguir leyéndose, no quedar teñido.
 */
export function fillOpacityFor(state: CountryState | undefined): number {
  if (!state || state.status === 'none') return 0
  return 0.14 + Math.min(state.cities + state.regions, 4) * 0.055
}

/** Países marcados (para el encuadre inicial y los contadores) */
export function visitedCodes(states: Map<string, CountryState>): string[] {
  return [...states.entries()].filter(([, s]) => s.status === 'visited').map(([code]) => code)
}
