import { ref } from 'vue'

// Buscador de aeropuertos (IATA) para los campos de origen/destino de un
// vuelo. El dataset (386 KB) se carga perezosamente la primera vez que se
// busca y se comparte entre todos los usos (form de reserva y editor de
// tramos).

export interface Airport {
  code: string
  name: string
  city: string
  country: string
}

let airportsCache: Airport[] | null = null

async function loadAirports(): Promise<Airport[]> {
  if (!airportsCache) {
    const raw = (await import('../data/airports.json')).default as [
      string, string, string, string,
    ][]
    airportsCache = raw.map(([code, name, city, country]) => ({ code, name, city, country }))
  }
  return airportsCache
}

export function useAirportSearch() {
  const airportOptions = ref<Airport[]>([])

  async function searchAirports(event: { query: string }) {
    const all = await loadAirports()
    const q = event.query.trim().toLowerCase()
    if (!q) {
      airportOptions.value = all.slice(0, 20)
      return
    }
    const code = q.toUpperCase()
    const byCode = all.filter((a) => a.code.startsWith(code))
    const byText = all.filter(
      (a) =>
        !a.code.startsWith(code) &&
        (a.city.toLowerCase().includes(q) || a.name.toLowerCase().includes(q)),
    )
    airportOptions.value = [...byCode, ...byText].slice(0, 20)
  }

  return { airportOptions, searchAirports }
}
