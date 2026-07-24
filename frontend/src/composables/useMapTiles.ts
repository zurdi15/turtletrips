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
  const attribution =
    '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
  return { url, attribution }
}
