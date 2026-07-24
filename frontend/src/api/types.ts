export type TripStatus = 'planning' | 'upcoming' | 'ongoing' | 'done'
export type PlaceCategory =
  | 'sight' | 'food' | 'museum' | 'nature' | 'viewpoint' | 'shopping' | 'city' | 'town' | 'other'
export type BookingType =
  | 'hotel' | 'flight' | 'train' | 'bus' | 'ferry' | 'car_rental' | 'activity' | 'other'

export interface Traveler {
  id: number
  name: string
  color: string | null
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
  notes: string | null
  travelers: Traveler[]
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

export interface PackingSelection {
  traveler_id: number | null
  template_id: number
}

export interface PackingTemplate {
  id: number
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

export interface Booking {
  id: number
  trip_id: number
  type: BookingType
  title: string
  provider: string | null
  confirmation_code: string | null
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
  notes: string | null
}

export interface Attachment {
  id: number
  trip_id: number
  booking_id: number | null
  original_name: string
  content_type: string
  size_bytes: number
  created_at: string
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

export type WorldPlaceKind = 'country' | 'city' | 'place'

export interface WorldPlace {
  id: number
  name: string
  kind: WorldPlaceKind
  country_code: string | null
  lat: number | null
  lon: number | null
  note: string | null
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
