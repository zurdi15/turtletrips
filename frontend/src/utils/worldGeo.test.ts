import { describe, expect, it } from 'vitest'
import type { Feature, MultiPolygon, Polygon } from 'geojson'
import {
  bboxWidthPx,
  boundsOf,
  featureBbox,
  isEmptyBbox,
  mainlandBbox,
  mainlandCenter,
  mergeBbox,
  normalizeLon,
  pointInFeature,
  ringArea,
} from './worldGeo'

function square(x: number, y: number, size: number): number[][] {
  return [
    [x, y],
    [x + size, y],
    [x + size, y + size],
    [x, y + size],
    [x, y],
  ]
}

const SIMPLE: Feature<Polygon> = {
  type: 'Feature',
  properties: {},
  geometry: { type: 'Polygon', coordinates: [square(0, 0, 2)] },
}

// "Francia sintética": el hexágono en Europa y una isla diminuta en el Pacífico
const WITH_ISLAND: Feature<MultiPolygon> = {
  type: 'Feature',
  properties: {},
  geometry: {
    type: 'MultiPolygon',
    coordinates: [[square(0, 42, 8)], [square(-150, -18, 1)]],
  },
}

describe('featureBbox', () => {
  it('abarca todas las partes', () => {
    const box = featureBbox(WITH_ISLAND)
    expect(box.minLon).toBe(-150)
    expect(box.maxLon).toBe(8)
  })
})

describe('mainlandBbox', () => {
  it('se queda con el anillo de mayor área e ignora las islas remotas', () => {
    const box = mainlandBbox(WITH_ISLAND)
    expect(box).toEqual({ minLon: 0, minLat: 42, maxLon: 8, maxLat: 50 })
  })

  it('en un polígono simple coincide con la caja completa', () => {
    expect(mainlandBbox(SIMPLE)).toEqual(featureBbox(SIMPLE))
  })

  it('devuelve una caja vacía sin geometría', () => {
    const empty = {
      type: 'Feature',
      properties: {},
      geometry: { type: 'MultiPolygon', coordinates: [] },
    } as Feature<MultiPolygon>
    expect(isEmptyBbox(mainlandBbox(empty))).toBe(true)
  })
})

describe('mainlandCenter', () => {
  it('centra el territorio principal, no el conjunto', () => {
    expect(mainlandCenter(WITH_ISLAND)).toEqual([46, 4])
  })
})

describe('ringArea', () => {
  it('mide el área sin importar el sentido de giro', () => {
    const ring = square(0, 0, 3)
    expect(ringArea(ring)).toBeCloseTo(9)
    expect(ringArea([...ring].reverse())).toBeCloseTo(9)
  })
})

describe('mergeBbox y boundsOf', () => {
  it('une cajas ignorando las vacías', () => {
    const a = featureBbox(SIMPLE)
    const merged = mergeBbox(a, { minLon: 10, minLat: 10, maxLon: 12, maxLat: 12 })
    expect(merged).toEqual({ minLon: 0, minLat: 0, maxLon: 12, maxLat: 12 })
  })

  it('boundsOf devuelve [[sur, oeste], [norte, este]]', () => {
    expect(boundsOf(featureBbox(SIMPLE))).toEqual([
      [0, 0],
      [2, 2],
    ])
  })
})

describe('bboxWidthPx', () => {
  it('crece con el zoom', () => {
    const box = featureBbox(SIMPLE)
    expect(bboxWidthPx(box, 3)).toBeCloseTo(bboxWidthPx(box, 2) * 2)
  })
})

describe('normalizeLon', () => {
  it('deja el rango normal como está', () => {
    expect(normalizeLon(0)).toBe(0)
    expect(normalizeLon(-179)).toBe(-179)
    expect(normalizeLon(179)).toBe(179)
  })

  it('trae de vuelta las copias del mundo que devuelve Leaflet al arrastrar', () => {
    expect(normalizeLon(200)).toBe(-160)
    expect(normalizeLon(-200)).toBe(160)
    expect(normalizeLon(540)).toBe(180 - 360)
  })
})

describe('pointInFeature', () => {
  it('dentro y fuera de un cuadrado', () => {
    expect(pointInFeature(SIMPLE, 1, 1)).toBe(true)
    expect(pointInFeature(SIMPLE, 5, 5)).toBe(false)
    expect(pointInFeature(SIMPLE, 1, -0.5)).toBe(false)
  })

  it('un agujero NO cuenta como país (el Vaticano dentro de Italia)', () => {
    const donut: Feature<Polygon> = {
      type: 'Feature',
      properties: {},
      geometry: { type: 'Polygon', coordinates: [square(0, 0, 10), square(4, 4, 2)] },
    }
    expect(pointInFeature(donut, 1, 1)).toBe(true)
    expect(pointInFeature(donut, 5, 5)).toBe(false) // dentro del agujero
  })

  it('recorre todos los polígonos de un multipolígono', () => {
    const islas: Feature<MultiPolygon> = {
      type: 'Feature',
      properties: {},
      geometry: { type: 'MultiPolygon', coordinates: [[square(0, 0, 2)], [square(20, 20, 2)]] },
    }
    expect(pointInFeature(islas, 21, 21)).toBe(true)
    expect(pointInFeature(islas, 10, 10)).toBe(false)
  })
})

