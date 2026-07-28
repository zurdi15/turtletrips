// Geometría de países: cajas, centroides y "territorio principal".
//
// Todo son funciones puras sobre GeoJSON — el mapa solo las consume.
import type { Feature, MultiPolygon, Polygon, Position } from 'geojson'

/** [[sur, oeste], [norte, este]] — el orden que espera Leaflet */
export type LatLngBoundsTuple = [[number, number], [number, number]]

export interface Bbox {
  minLon: number
  minLat: number
  maxLon: number
  maxLat: number
}

export function emptyBbox(): Bbox {
  return { minLon: Infinity, minLat: Infinity, maxLon: -Infinity, maxLat: -Infinity }
}

export function isEmptyBbox(box: Bbox): boolean {
  return !Number.isFinite(box.minLon) || !Number.isFinite(box.minLat)
}

/** Estira la caja para incluir todos los puntos del anillo */
export function extendBbox(box: Bbox, ring: Position[]): Bbox {
  for (const [lon, lat] of ring) {
    if (lon < box.minLon) box.minLon = lon
    if (lat < box.minLat) box.minLat = lat
    if (lon > box.maxLon) box.maxLon = lon
    if (lat > box.maxLat) box.maxLat = lat
  }
  return box
}

export function mergeBbox(a: Bbox, b: Bbox): Bbox {
  if (isEmptyBbox(a)) return { ...b }
  if (isEmptyBbox(b)) return { ...a }
  return {
    minLon: Math.min(a.minLon, b.minLon),
    minLat: Math.min(a.minLat, b.minLat),
    maxLon: Math.max(a.maxLon, b.maxLon),
    maxLat: Math.max(a.maxLat, b.maxLat),
  }
}

export function boundsOf(box: Bbox): LatLngBoundsTuple {
  return [
    [box.minLat, box.minLon],
    [box.maxLat, box.maxLon],
  ]
}

/** Anillos exteriores de un feature (los agujeros no cuentan para nada de esto) */
export function outerRings(feature: Feature<Polygon | MultiPolygon>): Position[][] {
  const geometry = feature.geometry
  if (!geometry) return []
  if (geometry.type === 'Polygon') return geometry.coordinates.slice(0, 1)
  return geometry.coordinates.map((polygon) => polygon[0]).filter(Boolean)
}

/** Caja de TODO el feature, islas remotas incluidas */
export function featureBbox(feature: Feature<Polygon | MultiPolygon>): Bbox {
  const box = emptyBbox()
  for (const ring of outerRings(feature)) extendBbox(box, ring)
  return box
}

/** Área con signo del anillo (fórmula del zapato); solo se usa su magnitud */
export function ringArea(ring: Position[]): number {
  let sum = 0
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    sum += (ring[j][0] + ring[i][0]) * (ring[j][1] - ring[i][1])
  }
  return Math.abs(sum / 2)
}

/**
 * Caja del TERRITORIO PRINCIPAL: la del anillo de mayor área, no la de todo el
 * país. Sin esto, encuadrar Francia se lleva el mapa a la Polinesia, Estados
 * Unidos a Guam y Noruega a Svalbard.
 */
export function mainlandBbox(feature: Feature<Polygon | MultiPolygon>): Bbox {
  let best: Position[] | null = null
  let bestArea = -1
  for (const ring of outerRings(feature)) {
    const area = ringArea(ring)
    if (area > bestArea) {
      bestArea = area
      best = ring
    }
  }
  return best ? extendBbox(emptyBbox(), best) : emptyBbox()
}

/** Centroide del territorio principal (media de los vértices de su anillo) */
export function mainlandCenter(
  feature: Feature<Polygon | MultiPolygon>,
): [number, number] | null {
  const box = mainlandBbox(feature)
  if (isEmptyBbox(box)) return null
  return [(box.minLat + box.maxLat) / 2, (box.minLon + box.maxLon) / 2]
}

/**
 * Longitud llevada a [-180, 180). Leaflet devuelve valores fuera del rango en
 * cuanto pasas a la copia siguiente del mundo arrastrando el mapa.
 */
export function normalizeLon(lon: number): number {
  return ((((lon + 180) % 360) + 360) % 360) - 180
}

/** Punto dentro de un anillo, por lanzamiento de rayo. Coordenadas [lon, lat] */
function pointInRing(ring: Position[], lon: number, lat: number): boolean {
  let inside = false
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i]
    const [xj, yj] = ring[j]
    if (yi > lat !== yj > lat && lon < ((xj - xi) * (lat - yi)) / (yj - yi) + xi) {
      inside = !inside
    }
  }
  return inside
}

/**
 * ¿Cae el punto dentro del país? Los anillos interiores son agujeros de verdad
 * (el Vaticano dentro de Italia, Lesoto dentro de Sudáfrica): un punto ahí NO
 * está en el país que lo rodea.
 */
export function pointInFeature(
  feature: Feature<Polygon | MultiPolygon>,
  lat: number,
  lon: number,
): boolean {
  const geometry = feature.geometry
  if (!geometry) return false
  const polygons =
    geometry.type === 'Polygon' ? [geometry.coordinates] : geometry.coordinates
  for (const rings of polygons) {
    if (!rings.length || !pointInRing(rings[0], lon, lat)) continue
    if (rings.slice(1).some((hole) => pointInRing(hole, lon, lat))) continue
    return true
  }
  return false
}

/** Ancho aparente del país en píxeles a un zoom dado (para decidir si cabe un marcador) */
export function bboxWidthPx(box: Bbox, zoom: number): number {
  if (isEmptyBbox(box)) return 0
  // 256 px por tile y 360° de mundo en el nivel 0
  const worldPx = 256 * 2 ** zoom
  return ((box.maxLon - box.minLon) / 360) * worldPx
}
