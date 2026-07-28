// Decoder mínimo de TopoJSON → GeoJSON.
//
// La geometría del mapa mundial viaja en TopoJSON (231 KB gzip frente a ~3 MB
// del GeoJSON equivalente): los arcos se comparten entre países vecinos y las
// coordenadas van cuantizadas y delta-codificadas. Aquí solo hace falta
// Polygon/MultiPolygon, así que son ~60 líneas puras en vez de la dependencia
// `topojson-client` (que arrastra `commander`).
import type { Feature, FeatureCollection, Polygon, MultiPolygon, Position } from 'geojson'

export interface TopoTransform {
  scale: [number, number]
  translate: [number, number]
}

export interface TopoGeometry {
  type: 'Polygon' | 'MultiPolygon'
  // Polygon: anillos de índices; MultiPolygon: polígonos de anillos de índices
  arcs: number[][] | number[][][]
  id?: string | number
  properties?: Record<string, unknown>
}

export interface Topology {
  type: 'Topology'
  transform?: TopoTransform
  arcs: number[][][]
  objects: Record<string, { type: string; geometries: TopoGeometry[] }>
}

/** Arcos absolutos: deshace la cuantización y el delta-encoding una sola vez */
function decodeArcs(topology: Topology): Position[][] {
  const transform = topology.transform
  return topology.arcs.map((arc) => {
    if (!transform) return arc.map(([x, y]) => [x, y] as Position)
    const [kx, ky] = transform.scale
    const [dx, dy] = transform.translate
    let x = 0
    let y = 0
    return arc.map(([ax, ay]) => {
      x += ax
      y += ay
      return [x * kx + dx, y * ky + dy] as Position
    })
  })
}

/**
 * Un anillo es una secuencia de arcos; el índice negativo `~i` significa "el
 * arco i al revés". Arcos consecutivos comparten su punto de unión, así que
 * del segundo en adelante se salta el primer punto.
 */
function buildRing(indexes: number[], arcs: Position[][]): Position[] {
  const ring: Position[] = []
  for (const index of indexes) {
    const arc = arcs[index < 0 ? ~index : index]
    if (!arc) continue
    const points = index < 0 ? [...arc].reverse() : arc
    for (let i = ring.length ? 1 : 0; i < points.length; i++) ring.push(points[i])
  }
  return ring
}

/**
 * Deshace el salto del antimeridiano: un anillo que cruza el ±180 (Rusia por
 * Chukotka, Fiyi, la Antártida) llega con la longitud "envuelta", y al pintarlo
 * en un plano el trazo cruza el mapa entero de lado a lado en forma de franja.
 * Se acumula un desfase de ±360 en cada salto para que el anillo sea continuo,
 * aunque acabe fuera del rango [-180, 180].
 */
function unwrapRing(ring: Position[]): { ring: Position[]; wrapped: boolean } {
  let offset = 0
  let wrapped = false
  const out: Position[] = []
  for (let i = 0; i < ring.length; i++) {
    if (i > 0) {
      const delta = ring[i][0] - ring[i - 1][0]
      if (delta > 180) offset -= 360
      else if (delta < -180) offset += 360
      if (offset !== 0) wrapped = true
    }
    out.push([ring[i][0] + offset, ring[i][1]])
  }
  return { ring: out, wrapped }
}

/**
 * Un polígono desenrollado se sale del mundo por un lado, así que se añade su
 * copia desplazada 360°: entre las dos, lo que cae dentro de [-180, 180] es
 * exactamente el país (la punta de Chukotka vuelve a salir junto a Alaska).
 */
function withWorldCopies(rings: Position[][]): Position[][][] {
  const unwrapped = rings.map(unwrapRing)
  if (!unwrapped.some((r) => r.wrapped)) return [rings]

  const lons = unwrapped.flatMap((r) => r.ring.map((p) => p[0]))
  const shift = Math.max(...lons) > 180 ? -360 : 360
  const shifted = unwrapped.map((r) => r.ring.map(([lon, lat]) => [lon + shift, lat] as Position))
  return [unwrapped.map((r) => r.ring), shifted]
}

/** Convierte un objeto del topology (p. ej. 'countries') en un FeatureCollection */
export function topoToGeoJson(
  topology: Topology,
  objectName: string,
): FeatureCollection<Polygon | MultiPolygon> {
  const object = topology.objects[objectName]
  if (!object) return { type: 'FeatureCollection', features: [] }
  const arcs = decodeArcs(topology)

  const features = object.geometries.map((geometry): Feature<Polygon | MultiPolygon> => {
    // los polígonos que cruzan el antimeridiano se desdoblan en dos, así que
    // hasta un Polygon puede acabar siendo MultiPolygon
    const polygons =
      geometry.type === 'Polygon'
        ? [(geometry.arcs as number[][]).map((ring) => buildRing(ring, arcs))]
        : (geometry.arcs as number[][][]).map((polygon) =>
            polygon.map((ring) => buildRing(ring, arcs)),
          )
    const coordinates = polygons.flatMap(withWorldCopies)

    return {
      type: 'Feature',
      id: geometry.id,
      properties: (geometry.properties ?? {}) as Feature['properties'],
      geometry:
        coordinates.length === 1 && geometry.type === 'Polygon'
          ? ({ type: 'Polygon', coordinates: coordinates[0] } as Polygon)
          : ({ type: 'MultiPolygon', coordinates } as MultiPolygon),
    }
  })

  return { type: 'FeatureCollection', features }
}
