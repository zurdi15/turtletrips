#!/usr/bin/env node
/**
 * Regenera la geometría del mapa mundial (public/geo/).
 *
 * NO corre en CI ni en el build de Docker: los ficheros están commiteados y
 * solo se regeneran a mano cuando cambian las fronteras o la lista de países.
 *
 *   node scripts/build-geo.mjs countries     # países (ADM0)
 *   node scripts/build-geo.mjs iso           # tabla ISO numérico → alpha-2
 *   node scripts/build-geo.mjs regions <ne_10m_admin_1_states_provinces.shp>
 *
 * FUENTES
 *
 * - Países: Natural Earth 1:50m admin-0, empaquetado como TopoJSON cuantizado
 *   por world-atlas. DOMINIO PÚBLICO (no exige atribución; aun así el mapa
 *   acredita "Fronteras: Natural Earth" junto al crédito de CARTO/OSM).
 *   241 features, 756 KB en disco / ~231 KB por la red con gzip.
 *   Se descarga tal cual, sin post-proceso: el artefacto de world-atlas ya es
 *   exactamente el que queremos.
 *
 *   Por qué 50m y no 110m: a la versión 110m le faltan 28 de los 194 países
 *   del selector (Andorra, Malta, Singapur, Vaticano, Maldivas y casi todo el
 *   Caribe y el Pacífico).
 *
 *   Por qué no geoBoundaries (lo que usa TREK): pesa 5-10 veces más y su
 *   `shapeISO` para regiones vale el ISO del PAÍS (las 19 regiones de España
 *   comparten "ESP"), así que no hay clave estable que guardar en la base.
 *
 * - Tabla ISO 3166-1: dataset `datasets/country-codes`. La geometría identifica
 *   cada país por su código NUMÉRICO, no alpha-2.
 *
 * - Regiones: Natural Earth 1:10m admin-1 (dominio público; hay que bajar el
 *   shapefile a mano desde naturalearthdata.com, son 15 MB comprimidos). Es el
 *   único dataset mundial con `iso_3166_2` de verdad — el `shapeISO` de
 *   geoBoundaries vale el ISO del PAÍS en todas las regiones del país.
 *   Un fichero por país (190 países, ~5 MB en total, de 3 KB a 418 KB según el
 *   país) que el mapa pide solo cuando ese país entra en pantalla.
 *   Para España, Francia e Italia se DISUELVEN las provincias en su comunidad
 *   / région / regione usando `region_cod` (ES.CT → ES-CT), que sí es el código
 *   ISO 3166-2 de la unidad grande.
 *
 * VERSIONADO: public/ no lleva hash de contenido, así que el nombre del fichero
 * incluye la versión (`.v1.`). Al regenerar con datos distintos, súbela aquí y
 * en COUNTRIES_URL de src/composables/useWorldGeometry.ts.
 */
import { execFileSync } from 'node:child_process'
import { mkdir, readdir, readFile, rm, writeFile } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'

const GEO_DIR = fileURLToPath(new URL('../public/geo/', import.meta.url))
const SRC_DIR = fileURLToPath(new URL('../src/', import.meta.url))

const COUNTRIES_SRC = 'https://unpkg.com/world-atlas@2.0.2/countries-50m.json'
const COUNTRIES_OUT = 'countries-50m.v1.topo.json'
const ISO_SRC =
  'https://raw.githubusercontent.com/datasets/country-codes/main/data/country-codes.csv'

async function get(url) {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText} — ${url}`)
  return res
}

async function buildCountries() {
  const res = await get(COUNTRIES_SRC)
  const body = Buffer.from(await res.arrayBuffer())
  await mkdir(GEO_DIR, { recursive: true })
  await writeFile(GEO_DIR + COUNTRIES_OUT, body)
  console.log(`✓ ${COUNTRIES_OUT} — ${(body.length / 1024).toFixed(0)} KB`)
}

/** CSV con comillas: parseo mínimo, suficiente para este fichero */
function parseCsv(text) {
  const rows = []
  let row = []
  let field = ''
  let quoted = false
  for (let i = 0; i < text.length; i++) {
    const ch = text[i]
    if (quoted) {
      if (ch === '"') {
        if (text[i + 1] === '"') (field += '"'), i++
        else quoted = false
      } else field += ch
    } else if (ch === '"') quoted = true
    else if (ch === ',') (row.push(field), (field = ''))
    else if (ch === '\n') (row.push(field), rows.push(row), (row = []), (field = ''))
    else if (ch !== '\r') field += ch
  }
  if (field || row.length) (row.push(field), rows.push(row))
  return rows
}

async function buildIso() {
  const res = await get(ISO_SRC)
  const rows = parseCsv(await res.text())
  const header = rows[0]
  const numeric = header.indexOf('ISO3166-1-numeric')
  const alpha2 = header.indexOf('ISO3166-1-Alpha-2')
  const pairs = new Map()
  for (const row of rows.slice(1)) {
    const n = (row[numeric] ?? '').trim()
    const a = (row[alpha2] ?? '').trim()
    if (n && a) pairs.set(n.padStart(3, '0'), a)
  }
  const entries = [...pairs.entries()].sort(([a], [b]) => a.localeCompare(b))
  const body = [
    '// Códigos ISO 3166-1: numérico → alpha-2.',
    '//',
    '// La geometría del mapa mundial (Natural Earth vía world-atlas) identifica cada',
    '// país por su código NUMÉRICO, no por alpha-2 — de paso esquiva el famoso -99',
    '// que Natural Earth pone en ISO_A2 para territorios en disputa.',
    '//',
    '// Generado desde datasets/country-codes (ISO 3166-1). Ver frontend/scripts/build-geo.mjs.',
    'const ALPHA2_BY_NUMERIC: Record<string, string> = {',
    ...entries.map(([n, a]) => `  '${n}': '${a}',`),
    '}',
    '',
    '/** alpha-2 del código numérico de un feature; null si no es un país ISO */',
    'export function alpha2FromNumeric(id: string | number | undefined | null): string | null {',
    '  if (id === undefined || id === null) return null',
    "  return ALPHA2_BY_NUMERIC[String(id).padStart(3, '0')] ?? null",
    '}',
    '',
    'export { ALPHA2_BY_NUMERIC }',
    '',
  ].join('\n')
  await writeFile(SRC_DIR + 'isoNumeric.ts', body)
  console.log(`✓ src/isoNumeric.ts — ${entries.length} entradas`)
}

/**
 * Se genera admin-1 para TODOS los países: con una lista curada, el mapa se
 * quedaba mudo en la mayoría (¿por qué Alemania sí y Grecia no?). Los únicos
 * que se quedan fuera son los que no tienen una unidad "región" utilizable:
 *
 *  · los DEMASIADO FINOS, donde admin-1 son distritos o municipios y marcarlos
 *    sería absurdo (medido sobre el propio shapefile, > 60 unidades con ISO):
 *    GB 232 distritos, SI 212 municipios, UG 134, LV 119, MK 84, TR 81
 *    provincias, MT 68 consejos locales, AZ 78.
 *  · los que se DISUELVEN aparte (abajo).
 *  · los que se quedan en UNA sola unidad: esa "región" es el país entero. Se
 *    detectan al generar, contando geometrías, no con otra lista a mano.
 */
const ADM1_TOO_FINE = ['GB', 'TR', 'SI', 'LV', 'MK', 'MT', 'UG', 'AZ']
/** aquí admin-1 son provincias: se disuelven en su comunidad/région/regione */
const ADM1_DISSOLVED = ['ES', 'FR', 'IT']
/** mínimo de regiones para que el fichero aporte algo */
const ADM1_MIN_UNITS = 2
/**
 * Simplificación por RESOLUCIÓN, no por porcentaje: se tiran los vértices que
 * describen detalles por debajo de ~600 m (≈1 px a zoom 6). A los zooms del mapa (≤ 10) no se
 * distingue del original, y evita el redondeo de esquinas del 12% anterior, que
 * es lo que hacía que las fronteras parecieran dibujadas a mano. Las
 * coordenadas se cuantizan además a 3 decimales (~110 m), como hace TREK.
 */
const SIMPLIFY = 'interval=600'

function mapshaper(args) {
  execFileSync('npx', ['--yes', 'mapshaper@0.6', ...args], { stdio: ['ignore', 'ignore', 'inherit'] })
}

async function buildRegions(shp) {
  if (!shp) throw new Error('falta la ruta al ne_10m_admin_1_states_provinces.shp')
  const out = GEO_DIR + 'adm1/'
  const tmp = out + '.tmp/'
  await mkdir(tmp, { recursive: true })

  // Natural Earth trae basura en iso_3166_2: espacios de más ("FR-IDF\t") y
  // rellenos "AU-X02~" para islas sin código ISO. El id acaba en la DB como
  // WorldPlace.region_code, así que se limpia y se descarta lo que no sea un
  // 3166-2 de verdad — esas unidades no se pueden marcar.
  const ISO_OK = 'iso_3166_2 = (iso_3166_2 || "").trim()'
  const ISO_VALID = '/^[A-Z]{2}-[A-Z0-9]{1,3}$/.test(iso_3166_2)'

  // simplificar ANTES de partir: así las fronteras compartidas siguen casando
  mapshaper([
    shp,
    '-filter', `!${JSON.stringify([...ADM1_TOO_FINE, ...ADM1_DISSOLVED])}.includes(iso_a2)`,
    '-each', ISO_OK,
    '-filter', ISO_VALID,
    '-filter-fields', 'iso_3166_2,iso_a2,name,name_es,name_en',
    '-simplify', SIMPLIFY, 'keep-shapes',
    '-clean',
    '-split', 'iso_a2',
    // `singles`: un fichero por capa (si no, TopoJSON las junta todas en uno)
    '-o', tmp, 'format=topojson', 'singles', 'id-field=iso_3166_2', 'precision=0.001',
  ])

  mapshaper([
    shp,
    '-filter', `${JSON.stringify(ADM1_DISSOLVED)}.includes(iso_a2)`,
    // el nombre de la unidad grande y su código ISO viven en region/region_cod
    '-dissolve', 'region_cod', 'copy-fields=iso_a2,region',
    '-each', 'iso_3166_2 = region_cod.replace(".", "-"), name = region',
    '-each', ISO_OK,
    '-filter', ISO_VALID,
    '-filter-fields', 'iso_3166_2,iso_a2,name',
    '-simplify', SIMPLIFY, 'keep-shapes',
    '-clean',
    '-split', 'iso_a2',
    '-o', tmp, 'format=topojson', 'singles', 'id-field=iso_3166_2', 'precision=0.001',
  ])

  let total = 0
  let written = 0
  const skipped = []
  for (const file of await readdir(tmp)) {
    const code = file.replace(/\.json$/, '').toUpperCase()
    const body = await readFile(tmp + file)
    const topology = JSON.parse(body.toString())
    const units = Object.values(topology.objects)[0]?.geometries?.length ?? 0
    // un país de una sola "región" es el país entero: no aporta nada y encima
    // el mapa ofrecería un botón que no cambia nada
    if (units < ADM1_MIN_UNITS) {
      skipped.push(`${code} (${units})`)
      continue
    }
    await writeFile(`${out}${code}.v1.topo.json`, body)
    total += body.length
    written += 1
  }
  await rm(tmp, { recursive: true, force: true })
  console.log(`✓ ${written} países · total ${(total / 1024).toFixed(0)} KB`)
  if (skipped.length) console.log(`  sin regiones útiles: ${skipped.join(', ')}`)
}

const target = process.argv[2] ?? 'countries'
if (target === 'countries') await buildCountries()
else if (target === 'iso') await buildIso()
else if (target === 'regions') await buildRegions(process.argv[3])
else {
  console.error(`objetivo desconocido: ${target} (countries | iso | regions)`)
  process.exit(1)
}
