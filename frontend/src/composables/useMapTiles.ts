import { computed } from 'vue'
import { useTheme } from './useTheme'

/**
 * Tiles de CARTO (sin API key): cartografía limpia con rotulación más
 * latinizada que el estilo por defecto de OSM, y variante oscura que
 * acompaña al tema de la app.
 */
export function useMapTiles() {
  const { isDark } = useTheme()
  const url = computed(() =>
    isDark.value
      ? 'https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png'
      : 'https://a.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png',
  )
  /**
   * La misma cartografía partida en dos: base SIN rótulos y solo-rótulos. El
   * mapa mundial mete su relleno entre las dos, así los nombres de países,
   * regiones y ciudades se leen POR ENCIMA del verde en vez de quedar tapados.
   */
  const baseUrl = computed(() =>
    isDark.value
      ? 'https://a.basemaps.cartocdn.com/rastertiles/dark_nolabels/{z}/{x}/{y}.png'
      : 'https://a.basemaps.cartocdn.com/rastertiles/voyager_nolabels/{z}/{x}/{y}.png',
  )
  const labelsUrl = computed(() =>
    isDark.value
      ? 'https://a.basemaps.cartocdn.com/rastertiles/dark_only_labels/{z}/{x}/{y}.png'
      : 'https://a.basemaps.cartocdn.com/rastertiles/voyager_only_labels/{z}/{x}/{y}.png',
  )
  // Natural Earth es dominio público y no exige atribución; el crédito va por
  // cortesía, junto al de la cartografía base
  const attribution =
    '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a> &middot; <a href="https://www.naturalearthdata.com/">Natural Earth</a>'
  return { url, baseUrl, labelsUrl, attribution }
}
