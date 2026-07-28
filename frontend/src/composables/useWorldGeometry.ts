import { ref, shallowRef } from 'vue'
import type { Feature, FeatureCollection, MultiPolygon, Polygon } from 'geojson'
import { alpha2FromNumeric } from '../isoNumeric'
import { topoToGeoJson, type Topology } from '../utils/topojson'
import {
  boundsOf,
  emptyBbox,
  extendBbox,
  featureBbox,
  mainlandBbox,
  mergeBbox,
  normalizeLon,
  outerRings,
  pointInFeature,
  type Bbox,
  type LatLngBoundsTuple,
} from '../utils/worldGeo'

// Geometría del mapa mundial: se descarga UNA vez por sesión (caché a nivel de
// módulo, como useCountryCenter) y el service worker la guarda 180 días.
//
// Vive en public/geo/ y no en src/: los .json de src/ acaban como chunks .js
// dentro del precache del SW, y serían 756 KB que descarga todo el mundo en
// cada deploy aunque no abra el mapa.
const COUNTRIES_URL = '/geo/countries-50m.v1.topo.json'
const REGIONS_URL = (code: string) => `/geo/adm1/${code}.v1.topo.json`
/** se muestran varios países a la vez y se vuelve sobre ellos al mover el mapa */
const REGION_CACHE_MAX = 40

export type CountryFeature = Feature<Polygon | MultiPolygon>

export interface CountryGeometry {
  /** referencia ESTABLE: vue-leaflet reconstruye la capa entera si cambia */
  geojson: FeatureCollection<Polygon | MultiPolygon>
  /** varios features por código: Australia aparece dos veces en Natural Earth */
  byCode: Map<string, CountryFeature[]>
  codeOf: (feature: CountryFeature) => string | null
  boundsOf: (code: string) => LatLngBoundsTuple | null
  centerOf: (code: string) => [number, number] | null
  /** país que hay bajo un punto del mapa (null en el mar) */
  countryAt: (lat: number, lon: number) => string | null
  /** países que asoman por la vista, del centro hacia fuera */
  countriesIn: (box: Bbox, max: number) => string[]
}

const geometry = shallowRef<CountryGeometry | null>(null)
const loading = ref(false)
let pending: Promise<CountryGeometry | null> | null = null

/**
 * El catch-all del backend sirve index.html con 200 para rutas inexistentes:
 * sin comprobar el content-type, un despliegue sin la geometría acabaría en un
 * `res.json()` reventado en vez de en un mapa sin relleno.
 */
async function fetchTopology(url: string): Promise<Topology | null> {
  try {
    const res = await fetch(url)
    if (!res.ok) return null
    if (!(res.headers.get('content-type') ?? '').includes('json')) return null
    return (await res.json()) as Topology
  } catch {
    return null
  }
}

function buildGeometry(topology: Topology): CountryGeometry {
  const geojson = topoToGeoJson(topology, 'countries')
  const byCode = new Map<string, CountryFeature[]>()
  const codes = new WeakMap<object, string | null>()

  for (const feature of geojson.features) {
    const code = alpha2FromNumeric(feature.id)
    codes.set(feature, code)
    if (!code) continue
    const list = byCode.get(code)
    if (list) list.push(feature)
    else byCode.set(code, [feature])
  }

  // el encuadre usa el TERRITORIO PRINCIPAL: con la caja completa, Francia se
  // lleva el mapa a la Polinesia y Estados Unidos a Guam
  const boxCache = new Map<string, Bbox>()
  function mainBox(code: string): Bbox | null {
    const cached = boxCache.get(code)
    if (cached) return cached
    const features = byCode.get(code)
    if (!features?.length) return null
    let box = emptyBbox()
    for (const feature of features) box = mergeBbox(box, mainlandBbox(feature))
    boxCache.set(code, box)
    return box
  }

  // cajas completas (islas incluidas) para descartar países de un vistazo antes
  // de meterse a mirar polígono a polígono
  const hitBoxes: { code: string; box: Bbox; feature: CountryFeature }[] = []
  // cajas por TROZO (cada anillo exterior): la de Francia entera cruza el
  // planeta por la Polinesia, así que para "¿qué países se ven?" hay que mirar
  // pedazo a pedazo o media Europa saldría desde cualquier parte
  const partBoxes: { code: string; box: Bbox }[] = []
  for (const feature of geojson.features) {
    const code = codes.get(feature)
    if (!code) continue
    hitBoxes.push({ code, box: featureBbox(feature), feature })
    for (const ring of outerRings(feature)) {
      partBoxes.push({ code, box: extendBbox(emptyBbox(), ring) })
    }
  }

  function countryAt(lat: number, lon: number): string | null {
    const x = normalizeLon(lon)
    for (const { code, box, feature } of hitBoxes) {
      if (lat < box.minLat || lat > box.maxLat || x < box.minLon || x > box.maxLon) continue
      if (pointInFeature(feature, lat, x)) return code
    }
    return null
  }

  return {
    geojson,
    byCode,
    codeOf: (feature) => codes.get(feature) ?? null,
    countryAt,
    countriesIn: (box, max) => {
      const midLat = (box.minLat + box.maxLat) / 2
      const midLon = (box.minLon + box.maxLon) / 2
      const nearest = new Map<string, number>()
      for (const part of partBoxes) {
        if (
          part.box.maxLat < box.minLat ||
          part.box.minLat > box.maxLat ||
          part.box.maxLon < box.minLon ||
          part.box.minLon > box.maxLon
        ) {
          continue
        }
        // distancia del trozo al centro de la pantalla (0 si lo contiene)
        const dLat = Math.max(part.box.minLat - midLat, 0, midLat - part.box.maxLat)
        const dLon = Math.max(part.box.minLon - midLon, 0, midLon - part.box.maxLon)
        const distance = dLat * dLat + dLon * dLon
        const best = nearest.get(part.code)
        if (best === undefined || distance < best) nearest.set(part.code, distance)
      }
      // el país que hay justo bajo el centro va primero: si el tope recorta,
      // que no se quede fuera precisamente el que estás mirando
      const focus = countryAt(midLat, midLon)
      if (focus) nearest.set(focus, -1)
      return [...nearest.entries()]
        .sort((a, b) => a[1] - b[1])
        .slice(0, max)
        .map(([code]) => code)
    },
    boundsOf: (code) => {
      const box = mainBox(code)
      return box ? boundsOf(box) : null
    },
    centerOf: (code) => {
      const box = mainBox(code)
      return box ? [(box.minLat + box.maxLat) / 2, (box.minLon + box.maxLon) / 2] : null
    },
  }
}

export interface RegionGeometry {
  /** referencia ESTABLE por país */
  geojson: FeatureCollection<Polygon | MultiPolygon>
  /** código ISO 3166-2 del feature ("ES-CT") */
  codeOf: (feature: CountryFeature) => string | null
  nameOf: (feature: CountryFeature) => string
}

// LRU cortito: la geometría del país que se está mirando y un par de vueltas atrás
const regionCache = new Map<string, RegionGeometry | null>()
const regionPending = new Map<string, Promise<RegionGeometry | null>>()

function buildRegions(topology: Topology): RegionGeometry | null {
  // cada fichero trae un único objeto, nombrado con el código del país
  const objectName = Object.keys(topology.objects)[0]
  if (!objectName) return null
  const geojson = topoToGeoJson(topology, objectName)
  const codes = new WeakMap<object, string | null>()
  const names = new WeakMap<object, string>()
  for (const feature of geojson.features) {
    codes.set(feature, feature.id ? String(feature.id) : null)
    names.set(feature, String(feature.properties?.name ?? feature.id ?? ''))
  }
  return {
    geojson,
    codeOf: (feature) => codes.get(feature) ?? null,
    nameOf: (feature) => names.get(feature) ?? '',
  }
}

export function useWorldGeometry() {
  async function load(): Promise<CountryGeometry | null> {
    if (geometry.value) return geometry.value
    if (pending) return pending
    loading.value = true
    pending = fetchTopology(COUNTRIES_URL)
      .then((topology) => {
        if (topology) geometry.value = buildGeometry(topology)
        return geometry.value
      })
      .finally(() => {
        loading.value = false
        pending = null
      })
    return pending
  }

  /**
   * Geometría de las regiones de un país. Devuelve null si ese país no tiene
   * fichero (solo hay una lista curada), y entonces la UI no ofrece regiones.
   */
  async function loadRegions(code: string): Promise<RegionGeometry | null> {
    if (regionCache.has(code)) {
      // Map conserva el orden de INSERCIÓN: sin re-insertar, la expulsión sería
      // por antigüedad y podría tirar justo el país que estás mirando
      const cached = regionCache.get(code) ?? null
      regionCache.delete(code)
      regionCache.set(code, cached)
      return cached
    }
    const inFlight = regionPending.get(code)
    if (inFlight) return inFlight

    const request = fetchTopology(REGIONS_URL(code))
      .then((topology) => {
        const geo = topology ? buildRegions(topology) : null
        // LRU: al llenarse, cae la entrada más antigua
        if (regionCache.size >= REGION_CACHE_MAX) {
          const oldest = regionCache.keys().next().value
          if (oldest) regionCache.delete(oldest)
        }
        regionCache.set(code, geo)
        return geo
      })
      .finally(() => regionPending.delete(code))

    regionPending.set(code, request)
    return request
  }

  return { geometry, loading, load, loadRegions, featureBbox }
}
