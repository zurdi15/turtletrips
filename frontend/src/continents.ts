import { COUNTRIES } from './countries'

// Continentes estilo "scratch map" (6): los transcontinentales van donde los
// pone el uso común de estos mapas (RU/CY en Europa; TR/GE/AM/AZ/KZ en Asia;
// EG en África; México, Centroamérica y Caribe en Norteamérica).

export type ContinentKey =
  | 'europe'
  | 'asia'
  | 'africa'
  | 'northAmerica'
  | 'southAmerica'
  | 'oceania'

export const CONTINENT_ORDER: ContinentKey[] = [
  'europe',
  'asia',
  'africa',
  'northAmerica',
  'southAmerica',
  'oceania',
]

export const CONTINENT_KEYS: Record<ContinentKey, string> = {
  europe: 'world.continents.europe',
  asia: 'world.continents.asia',
  africa: 'world.continents.africa',
  northAmerica: 'world.continents.northAmerica',
  southAmerica: 'world.continents.southAmerica',
  oceania: 'world.continents.oceania',
}

// prettier-ignore
const CODES: Record<ContinentKey, string[]> = {
  europe: [
    'AL', 'AD', 'AT', 'BE', 'BY', 'BA', 'BG', 'CH', 'CY', 'CZ', 'DE', 'DK',
    'EE', 'ES', 'FI', 'FR', 'GB', 'GR', 'HR', 'HU', 'IE', 'IS', 'IT', 'LI',
    'LT', 'LU', 'LV', 'MC', 'MD', 'ME', 'MK', 'MT', 'NL', 'NO', 'PL', 'PT',
    'RO', 'RS', 'RU', 'SE', 'SI', 'SK', 'SM', 'UA', 'VA',
  ],
  asia: [
    'AE', 'AF', 'AM', 'AZ', 'BD', 'BH', 'BN', 'BT', 'CN', 'GE', 'ID', 'IL',
    'IN', 'IQ', 'IR', 'JO', 'JP', 'KG', 'KH', 'KP', 'KR', 'KW', 'KZ', 'LA',
    'LB', 'LK', 'MM', 'MN', 'MV', 'MY', 'NP', 'OM', 'PH', 'PK', 'PS', 'QA',
    'SA', 'SG', 'SY', 'TH', 'TJ', 'TL', 'TM', 'TR', 'TW', 'UZ', 'VN', 'YE',
  ],
  africa: [
    'AO', 'BF', 'BI', 'BJ', 'BW', 'CD', 'CF', 'CG', 'CI', 'CM', 'CV', 'DJ',
    'DZ', 'EG', 'ER', 'ET', 'GA', 'GH', 'GM', 'GN', 'GQ', 'GW', 'KE', 'KM',
    'LR', 'LS', 'LY', 'MA', 'MG', 'ML', 'MR', 'MU', 'MW', 'MZ', 'NA', 'NE',
    'NG', 'RW', 'SC', 'SD', 'SL', 'SN', 'SO', 'SS', 'ST', 'SZ', 'TD', 'TG',
    'TN', 'TZ', 'UG', 'ZA', 'ZM', 'ZW',
  ],
  northAmerica: [
    'AG', 'BB', 'BS', 'BZ', 'CA', 'CR', 'CU', 'DM', 'DO', 'GD', 'GT', 'HN',
    'HT', 'JM', 'KN', 'LC', 'MX', 'NI', 'PA', 'SV', 'TT', 'US', 'VC',
  ],
  southAmerica: ['AR', 'BO', 'BR', 'CL', 'CO', 'EC', 'GY', 'PE', 'PY', 'SR', 'UY', 'VE'],
  oceania: ['AU', 'FJ', 'FM', 'KI', 'MH', 'NR', 'NZ', 'PG', 'PW', 'SB', 'TO', 'TV', 'VU', 'WS'],
}

export const CONTINENT_BY_CODE: Map<string, ContinentKey> = new Map(
  CONTINENT_ORDER.flatMap((key) => CODES[key].map((code) => [code, key] as [string, ContinentKey])),
)

export interface ContinentStat {
  key: ContinentKey
  visited: number
  total: number
}

/** visitados/total por continente, sobre el listado de países de la app */
export function continentStats(visitedCodes: Iterable<string>): ContinentStat[] {
  const totals = new Map<ContinentKey, number>()
  for (const country of COUNTRIES) {
    const key = CONTINENT_BY_CODE.get(country.code)
    if (key) totals.set(key, (totals.get(key) ?? 0) + 1)
  }
  const visited = new Map<ContinentKey, Set<string>>()
  for (const code of new Set(visitedCodes)) {
    const key = CONTINENT_BY_CODE.get(code)
    if (!key) continue
    const set = visited.get(key) ?? new Set()
    set.add(code)
    visited.set(key, set)
  }
  return CONTINENT_ORDER.map((key) => ({
    key,
    visited: visited.get(key)?.size ?? 0,
    total: totals.get(key) ?? 0,
  }))
}
