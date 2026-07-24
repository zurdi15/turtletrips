import type { BookingType, PlaceCategory, TripStatus } from './api/types'

export const TRIP_STATUS_LABELS: Record<TripStatus, string> = {
  planning: 'Planificando',
  upcoming: 'Próximo',
  ongoing: 'En curso',
  done: 'Terminado',
}

export const TRIP_STATUS_SEVERITY: Record<TripStatus, string> = {
  planning: 'info',
  upcoming: 'warn',
  ongoing: 'success',
  done: 'secondary',
}

export const PLACE_CATEGORY_LABELS: Record<PlaceCategory, string> = {
  city: 'Ciudad',
  town: 'Pueblo',
  sight: 'Monumento',
  food: 'Comida',
  museum: 'Museo',
  nature: 'Naturaleza',
  viewpoint: 'Mirador',
  shopping: 'Compras',
  other: 'Otro',
}

export const PLACE_CATEGORY_COLORS: Record<PlaceCategory, string> = {
  city: '#0f766e',
  town: '#84cc16',
  sight: '#e11d48',
  food: '#f59e0b',
  museum: '#8b5cf6',
  nature: '#16a34a',
  viewpoint: '#0ea5e9',
  shopping: '#ec4899',
  other: '#64748b',
}

export const PLACE_CATEGORY_ICONS: Record<PlaceCategory, string> = {
  city: 'pi pi-building',
  town: 'pi pi-home',
  sight: 'pi pi-building-columns',
  food: 'pi pi-shop',
  museum: 'pi pi-warehouse',
  nature: 'pi pi-sun',
  viewpoint: 'pi pi-camera',
  shopping: 'pi pi-shopping-bag',
  other: 'pi pi-map-marker',
}

export const BOOKING_TYPE_LABELS: Record<BookingType, string> = {
  hotel: 'Hotel',
  flight: 'Vuelo',
  train: 'Tren',
  bus: 'Bus',
  ferry: 'Ferry',
  car_rental: 'Coche de alquiler',
  activity: 'Actividad',
  other: 'Otro',
}

export const BOOKING_TYPE_ICONS: Record<BookingType, string> = {
  hotel: 'pi pi-home',
  flight: 'pi pi-send',
  train: 'pi pi-arrow-right-arrow-left',
  bus: 'pi pi-truck',
  ferry: 'pi pi-compass',
  car_rental: 'pi pi-car',
  activity: 'pi pi-ticket',
  other: 'pi pi-bookmark',
}

// paleta de colores para categorías y viajeros (settings)
export const CATEGORY_PALETTE = [
  '#f59e0b', '#0ea5e9', '#8b5cf6', '#16a34a', '#e11d48', '#ec4899',
  '#f97316', '#6366f1', '#0f766e', '#84cc16', '#64748b', '#94a3b8',
]

// Monedas soportadas por frankfurter (BCE) más las habituales
export const CURRENCIES = [
  'EUR', 'USD', 'GBP', 'JPY', 'CHF', 'AUD', 'BGN', 'BRL', 'CAD', 'CNY',
  'CZK', 'DKK', 'HKD', 'HUF', 'IDR', 'ILS', 'INR', 'ISK', 'KRW', 'MXN',
  'MYR', 'NOK', 'NZD', 'PHP', 'PLN', 'RON', 'SEK', 'SGD', 'THB', 'TRY', 'ZAR',
]

export const MEMBER_COLORS = [
  '#0ea5e9', '#f59e0b', '#16a34a', '#e11d48', '#8b5cf6', '#ec4899', '#64748b',
]

export function toSelectOptions<T extends string>(labels: Record<T, string>) {
  return (Object.entries(labels) as [T, string][]).map(([value, label]) => ({ value, label }))
}
