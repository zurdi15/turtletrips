import { describe, expect, it } from 'vitest'
// ?raw: se lee el fichero REAL que sirve la app sin que TypeScript infiera el
// tipo literal de 756 KB de JSON (y sin necesitar @types/node en los tests)
import worldRaw from '../../public/geo/countries-50m.v1.topo.json?raw'
import { topoToGeoJson, type Topology } from './topojson'
import { alpha2FromNumeric } from '../isoNumeric'
import { COUNTRIES } from '../countries'
import { featureBbox, mainlandBbox, normalizeLon, pointInFeature } from './worldGeo'

// Topología a mano: un cuadrado partido en dos arcos, y un segundo polígono
// que reutiliza uno de esos arcos AL REVÉS (~i) — que es justo lo que hace el
// fichero real entre países vecinos.
const TOY: Topology = {
  type: 'Topology',
  transform: { scale: [1, 1], translate: [0, 0] },
  arcs: [
    // 0: (0,0) → (2,0)   [delta-codificado]
    [
      [0, 0],
      [2, 0],
    ],
    // 1: (2,0) → (2,2)   — la frontera COMPARTIDA por los dos polígonos
    [
      [2, 0],
      [0, 2],
    ],
    // 2: (2,2) → (0,2) → (0,0)
    [
      [2, 2],
      [-2, 0],
      [0, -2],
    ],
    // 3: (2,0) → (4,0) → (4,2) → (2,2)
    [
      [2, 0],
      [2, 0],
      [0, 2],
      [-2, 0],
    ],
  ],
  objects: {
    units: {
      type: 'GeometryCollection',
      geometries: [
        { type: 'Polygon', arcs: [[0, 1, 2]], id: '724', properties: { name: 'Izquierda' } },
        { type: 'Polygon', arcs: [[3, -2]], id: '250', properties: { name: 'Derecha' } },
      ],
    },
  },
}

describe('topoToGeoJson', () => {
  it('deshace la cuantización y el delta-encoding', () => {
    const { features } = topoToGeoJson(TOY, 'units')
    expect(features).toHaveLength(2)
    expect(features[0].geometry.coordinates[0]).toEqual([
      [0, 0],
      [2, 0],
      [2, 2],
      [0, 2],
      [0, 0],
    ])
  })

  it('recorre al revés los arcos con índice negativo y no repite el punto compartido', () => {
    const { features } = topoToGeoJson(TOY, 'units')
    const ring = features[1].geometry.coordinates[0] as number[][]
    // el arco ~1 aporta (2,2) → (2,0), sin duplicar el (2,2) que ya venía
    expect(ring).toEqual([
      [2, 0],
      [4, 0],
      [4, 2],
      [2, 2],
      [2, 0],
    ])
  })

  it('conserva id y properties', () => {
    const { features } = topoToGeoJson(TOY, 'units')
    expect(features[0].id).toBe('724')
    expect(features[0].properties?.name).toBe('Izquierda')
  })

  it('devuelve vacío si el objeto no existe', () => {
    expect(topoToGeoJson(TOY, 'nope').features).toEqual([])
  })
})

// --- golden test contra el fichero real que sirve la app ---

const world = topoToGeoJson(JSON.parse(worldRaw) as Topology, 'countries')
const byCode = new Map<string, (typeof world.features)[number]>()
for (const feature of world.features) {
  const code = alpha2FromNumeric(feature.id)
  if (code && !byCode.has(code)) byCode.set(code, feature)
}

/** mayor salto de longitud entre puntos consecutivos de cualquier anillo */
function maxLonJump(feature: (typeof world.features)[number]): number {
  const polygons =
    feature.geometry.type === 'Polygon'
      ? [feature.geometry.coordinates]
      : feature.geometry.coordinates
  let max = 0
  for (const polygon of polygons) {
    for (const ring of polygon) {
      for (let i = 1; i < ring.length; i++) {
        max = Math.max(max, Math.abs(ring[i][0] - ring[i - 1][0]))
      }
    }
  }
  return max
}

describe('antimeridiano', () => {
  it('desenrolla el anillo y añade su copia desplazada', () => {
    // cuadrado a caballo del ±180: (170,0) → (-170,0) → (-170,10) → (170,10)
    const crossing: Topology = {
      type: 'Topology',
      transform: { scale: [1, 1], translate: [0, 0] },
      arcs: [
        // el dato llega "envuelto": 170 → -170 → -170 → 170 → 170
        [
          [170, 0],
          [-340, 0],
          [0, 10],
          [340, 0],
          [0, -10],
        ],
      ],
      objects: {
        units: {
          type: 'GeometryCollection',
          geometries: [{ type: 'Polygon', arcs: [[0]], id: '643' }],
        },
      },
    }
    const { features } = topoToGeoJson(crossing, 'units')
    expect(features[0].geometry.type).toBe('MultiPolygon')
    const polygons = features[0].geometry.coordinates as number[][][][]
    expect(polygons).toHaveLength(2)
    // sin saltos: el primero sigue hacia el este (190) y el segundo es su copia
    expect(maxLonJump(features[0])).toBeLessThan(180)
    expect(Math.max(...polygons[0][0].map((p) => p[0]))).toBeGreaterThan(180)
    expect(Math.min(...polygons[1][0].map((p) => p[0]))).toBeLessThan(-180)
  })
})

describe('geometría real de países', () => {
  it('ningún país cruza el antimeridiano de un salto', () => {
    // Rusia, Fiyi y la Antártida lo cruzan en el dato original: sin tratarlos,
    // el trazo pinta franjas horizontales de lado a lado del mapa
    const worst = world.features
      .map((f) => ({ id: f.id, jump: maxLonJump(f) }))
      .filter((f) => f.jump > 180)
    expect(worst).toEqual([])
  })

  it('Rusia conserva Chukotka al otro lado del meridiano', () => {
    const russia = byCode.get('RU')!
    const lons = (russia.geometry.coordinates as number[][][][])
      .flat(2)
      .map((p) => p[0])
    expect(Math.min(...lons)).toBeLessThan(-170)
    expect(Math.max(...lons)).toBeGreaterThan(170)
  })

  it('trae los 241 países de Natural Earth 50m', () => {
    expect(world.features).toHaveLength(241)
  })

  it('cubre todos los países del selector menos Tuvalu', () => {
    const missing = COUNTRIES.map((c) => c.code).filter((code) => !byCode.has(code))
    expect(missing).toEqual(['TV'])
  })

  it('cierra los anillos y sitúa España donde toca', () => {
    const spain = byCode.get('ES')!
    const box = mainlandBbox(spain)
    expect(box.minLon).toBeGreaterThan(-10)
    expect(box.maxLon).toBeLessThan(5)
    expect(box.minLat).toBeGreaterThan(35)
    expect(box.maxLat).toBeLessThan(44)
    const ring = spain.geometry.coordinates.flat().at(0) as number[][]
    expect(ring[0]).toEqual(ring[ring.length - 1])
  })

  it('el territorio principal de Francia deja fuera los territorios de ultramar', () => {
    const france = byCode.get('FR')!
    // la caja completa cruza el planeta entero (Guayana, Reunión, Polinesia…)
    expect(featureBbox(france).maxLon - featureBbox(france).minLon).toBeGreaterThan(100)
    const box = mainlandBbox(france)
    expect(box.minLon).toBeGreaterThan(-6)
    expect(box.maxLon).toBeLessThan(10)
    expect(box.minLat).toBeGreaterThan(41)
    expect(box.maxLat).toBeLessThan(52)
  })
})

describe('país bajo un punto (geometría real)', () => {
  /** lo que hace `countryAt`: caja como filtro y luego el polígono */
  function countryAt(lat: number, lon: number): string | null {
    const x = normalizeLon(lon)
    for (const [code, feature] of byCode) {
      const box = featureBbox(feature)
      if (lat < box.minLat || lat > box.maxLat || x < box.minLon || x > box.maxLon) continue
      if (pointInFeature(feature, lat, x)) return code
    }
    return null
  }

  it('acierta el país de capitales conocidas', () => {
    expect(countryAt(51.1, 10.4)).toBe('DE') // centro de Alemania
    expect(countryAt(40.4, -3.7)).toBe('ES') // Madrid
    expect(countryAt(35.7, 139.7)).toBe('JP') // Tokio
    expect(countryAt(-33.9, 151.2)).toBe('AU') // Sídney
  })

  it('en mar abierto no hay país', () => {
    expect(countryAt(30, -40)).toBeNull() // Atlántico norte
  })

  it('funciona en las copias del mundo que devuelve Leaflet al arrastrar', () => {
    // Madrid una vuelta entera a la derecha
    expect(countryAt(40.4, -3.7 + 360)).toBe('ES')
    // Chukotka, al otro lado del ±180
    expect(countryAt(66, 179)).toBe('RU')
    // Fiyi se pisa el antimeridiano: al este solo lo cubre la copia desplazada
    expect(countryAt(-17.8, 178)).toBe('FJ')
    expect(countryAt(-16.8, -179.9)).toBe('FJ')
  })
})
