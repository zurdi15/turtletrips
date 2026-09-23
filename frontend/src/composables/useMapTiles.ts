import { computed } from 'vue'
import { useTheme } from './useTheme'

/**
 * Teselas de Esri (ArcGIS Online, sin API key): rotulación LATINIZADA junto a
 * la local ("台北市 / Tai Bei Shi"), que es lo que buscábamos en CARTO —
 * en 2026 empezó a estampar "API KEY REQUIRED" en todas sus teselas gratuitas.
 * Basta con citar la fuente (ver `attribution`).
 *
 * Los mapas de viaje usan una capa en claro y DOS en oscuro (el canvas oscuro
 * de Esri separa base y rótulos), de ahí que `layers` sea una lista.
 */
const ESRI = 'https://server.arcgisonline.com/ArcGIS/rest/services'
const tile = (service: string) => `${ESRI}/${service}/MapServer/tile/{z}/{y}/{x}`

export function useMapTiles() {
  const { isDark } = useTheme()

  /** capas de un mapa normal (sitios, selector de ubicación), en orden */
  const layers = computed(() =>
    isDark.value
      ? [tile('Canvas/World_Dark_Gray_Base'), tile('Canvas/World_Dark_Gray_Reference')]
      : [tile('World_Street_Map')],
  )

  /**
   * La misma cartografía partida en dos: base SIN rótulos y solo-rótulos. El
   * mapa mundial mete su relleno entre las dos, así los nombres de países,
   * regiones y ciudades se leen POR ENCIMA del verde en vez de quedar tapados.
   */
  const baseUrl = computed(() =>
    tile(isDark.value ? 'Canvas/World_Dark_Gray_Base' : 'Canvas/World_Light_Gray_Base'),
  )
  const labelsUrl = computed(() =>
    tile(isDark.value ? 'Canvas/World_Dark_Gray_Reference' : 'Canvas/World_Light_Gray_Reference'),
  )

  // Esri pide citar la fuente de sus basemaps; Natural Earth (dominio público)
  // va por cortesía, como antes
  const attribution =
    'Teselas &copy; <a href="https://www.esri.com/">Esri</a> &middot; Esri, HERE, Garmin, &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &middot; <a href="https://www.naturalearthdata.com/">Natural Earth</a>'
  return { layers, baseUrl, labelsUrl, attribution }
}
