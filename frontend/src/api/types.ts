export type TripStatus = 'planning' | 'upcoming' | 'ongoing' | 'done'
export type PlaceCategory =
  | 'sight' | 'food' | 'museum' | 'nature' | 'viewpoint' | 'shopping' | 'city' | 'town' | 'lodging' | 'other'
export type BookingType =
  | 'hotel' | 'flight' | 'train' | 'bus' | 'ferry' | 'car_rental' | 'activity' | 'other'

export interface Traveler {
  id: number
  name: string
  color: string | null
  family_id: number | null
  // ya trae ?v= de cache-bust; null si no hay foto
  avatar_url: string | null
  // true si el viajero tiene cuenta de usuario vinculada
  has_user: boolean
}

// --- sesión y administración ---

export type ThemePref = 'light' | 'dark' | 'system'
export type UiLanguage = 'es' | 'en'

export interface Family {
  id: number
  name: string
}

export interface SessionUser {
  id: number
  username: string
  is_admin: boolean
  theme: ThemePref
  language: UiLanguage
}

export interface Me {
  user: SessionUser
  traveler: Traveler
  family: Family | null
}

export interface User {
  id: number
  username: string
  is_admin: boolean
  traveler: Traveler
}

export interface LoginInput {
  username: string
  password: string
}

export interface BootstrapInput {
  username: string
  password: string
  traveler_name: string
  // idioma activo en la pantalla de login: la cuenta nace con él
  language?: UiLanguage
}

export interface SettingsInput {
  theme?: ThemePref
  language?: UiLanguage
}

// vincular un viajero existente O crear uno nuevo (exactamente uno de los dos)
export type UserCreateInput = {
  username: string
  password: string
  is_admin: boolean
  family_id?: number | null
} & ({ traveler_id: number } | { traveler_name: string })

export interface UserUpdateInput {
  is_admin?: boolean
}

export interface FamilyInput {
  name: string
}

export interface Trip {
  id: number
  name: string
  countries: string[]
  cover_url: string | null
  start_date: string | null
  end_date: string | null
  status: TripStatus
  status_override: TripStatus | null
  base_currency: string
  budget_amount: number | null
  album_url: string | null
  ics_token: string | null
  notes: string | null
  travelers: Traveler[]
  // true si hay liquidaciones registradas y los saldos quedan a cero
  debts_settled: boolean
  created_at: string
  updated_at: string
}

export interface Category {
  id: number
  kind: 'expense' | 'packing'
  name: string
  color: string | null
  position: number
}

export interface PackingItem {
  id: number
  trip_id: number
  traveler_id: number | null
  name: string
  category: string
  url: string | null
  checked: boolean
}

export interface ChecklistItem {
  id: number
  trip_id: number
  title: string
  done: boolean
  due_date: string | null
  url: string | null
  notes: string | null
}

export interface PackingSelection {
  traveler_id: number | null
  template_id: number
}

export interface PackingTemplate {
  id: number
  traveler_id: number // dueño (viajero con cuenta o virtual de la familia)
  name: string
  item_count: number
}

export interface PackingTemplateItem {
  id: number
  template_id: number
  name: string
  category: string
  url: string | null
}

export interface PackingTemplateDetail {
  id: number
  traveler_id: number
  name: string
  items: PackingTemplateItem[]
}

export interface Place {
  id: number
  trip_id: number
  name: string
  category: PlaceCategory
  notes: string | null
  url: string | null
  address: string | null
  lat: number | null
  lon: number | null
  visited: boolean
  priority: number
}

export interface ItineraryItem {
  id: number
  trip_id: number
  day: string
  end_day: string | null
  start_time: string | null
  end_time: string | null
  order_index: number
  title: string
  notes: string | null
  place_id: number | null
  booking_id: number | null
}

// diario + postal por día del itinerario (único por trip_id + day)
export interface DayJournal {
  id: number
  trip_id: number
  day: string // "YYYY-MM-DD"
  text: string | null
  photo_url: string | null
}

export interface Booking {
  id: number
  trip_id: number
  type: BookingType
  title: string
  provider: string | null
  confirmation_code: string | null
  flight_number: string | null
  start_dt: string | null
  end_dt: string | null
  origin: string | null
  destination: string | null
  address: string | null
  lat: number | null
  lon: number | null
  cost_amount: number | null
  cost_currency: string | null
  notes: string | null
  place_id: number | null
  paid_by_id: number | null
  paid_by_common: boolean
}

export type SplitMode = 'equal' | 'amount' | 'percent'

export interface ExpenseShare {
  traveler_id: number
  // null en modo equal (solo participación); importe o porcentaje en los demás
  value: number | null
}

export interface Expense {
  id: number
  trip_id: number
  booking_id: number | null
  place_id: number | null
  day: string
  category: string
  description: string
  amount: number
  currency: string
  exchange_rate: number
  amount_base: number
  paid_by_id: number | null
  // pagado del fondo común (excluyente con paid_by_id): no entra en los saldos
  paid_by_common: boolean
  split_mode: SplitMode
  shares: ExpenseShare[]
  notes: string | null
}

export interface Attachment {
  id: number
  trip_id: number
  booking_id: number | null
  expense_id: number | null
  original_name: string
  content_type: string
  size_bytes: number
  created_at: string
}

export interface DayForecast {
  day: string
  weather_code: number // código WMO de Open-Meteo
  t_max: number
  t_min: number
  precip_prob: number | null
}

export interface YearStats {
  year: number
  trips: number
  days: number
  countries: string[] // códigos ISO tocados ese año
  new_countries: string[] // estrenados ese año
  spent: { currency: string; amount: number }[]
}

export interface CategoryTotal { category: string; total: number }
export interface DayTotal { day: string; total: number }
export interface PayerTotal { member_id: number | null; name: string; total: number }
export interface CurrencyTotal { currency: string; amount: number }

export interface TripSummary {
  base_currency: string
  total_base: number
  budget_amount: number | null
  remaining: number | null
  expense_count: number
  by_category: CategoryTotal[]
  by_day: DayTotal[]
  by_payer: PayerTotal[]
  by_currency: CurrencyTotal[]
}

export interface TravelerBalance {
  traveler_id: number
  name: string
  color: string | null
  paid_base: number
  owed_base: number
  net_base: number // >0 le deben, <0 debe
}

export interface SettlementTransfer {
  from_id: number
  from_name: string
  to_id: number
  to_name: string
  amount_base: number
}

export interface PaidSettlement {
  id: number
  from_id: number
  from_name: string
  to_id: number
  to_name: string
  amount_base: number
  created_at: string
}

export interface TripBalances {
  base_currency: string
  balances: TravelerBalance[]
  settlements: SettlementTransfer[]
  paid_settlements: PaidSettlement[]
  debts_settled: boolean
  unassigned_count: number
  unassigned_total_base: number
  common_count: number
  common_total_base: number
}

export type WorldPlaceKind = 'country' | 'city' | 'place'

export interface WorldPlace {
  id: number
  name: string
  kind: WorldPlaceKind
  country_code: string | null
  lat: number | null
  lon: number | null
  note: string | null
  visited_year: number | null
  visited_month: number | null // 1-12
  photo_url: string | null
  auto: boolean
  origin: string | null
}

export interface GeocodeResult {
  display_name: string
  lat: number
  lon: number
}

export interface RateRead {
  base: string
  quote: string
  day: string
  rate: number
  source: string
}

// --- payloads de creación/edición (derivados de las entidades; los widenings
// number | string existen porque los formularios mandan strings) ---

export type TripInput = Partial<
  Omit<Trip, 'id' | 'status' | 'travelers' | 'created_at' | 'updated_at' | 'cover_url' | 'budget_amount'>
> & { budget_amount?: number | string | null; traveler_ids?: number[] }
export type PlaceInput = Partial<Omit<Place, 'id' | 'trip_id'>>
export type BookingInput = Partial<Omit<Booking, 'id' | 'trip_id' | 'cost_amount'>> & {
  cost_amount?: number | string | null
}
export type ExpenseInput = Partial<
  Omit<Expense, 'id' | 'trip_id' | 'amount' | 'exchange_rate' | 'amount_base'>
> & { amount?: number | string; exchange_rate?: number | string | null }
export type ItineraryInput = Partial<Omit<ItineraryItem, 'id' | 'trip_id'>>
export type PackingInput = Partial<Omit<PackingItem, 'id' | 'trip_id'>>
export type ChecklistInput = Partial<Omit<ChecklistItem, 'id' | 'trip_id'>>
export type WorldPlaceInput = Partial<Omit<WorldPlace, 'id' | 'auto' | 'origin'>>

export interface ImportRowError { row: number; error: string }
export interface ImportPreviewRow {
  row: number
  day: string
  category: string
  description: string
  amount: number
  currency: string
  exchange_rate: number
  amount_base: number
  paid_by: string | null
  place: string | null
  notes: string | null
}
export interface ImportResult {
  dry_run: boolean
  valid_rows: ImportPreviewRow[]
  errors: ImportRowError[]
  imported: number
}
