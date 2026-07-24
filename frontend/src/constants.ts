import type { BookingType, PlaceCategory, TripStatus } from './api/types'

export const TRIP_STATUS_LABELS: Record<TripStatus, string> = {
  planning: 'Planificando',
  upcoming: 'Próximo',
  ongoing: 'En curso',
  done: 'Terminado',
}

export const TRIP_STATUS_SEVERITY: Record<TripStatus, string> = {
  planning: 'info',
  upcoming: 'success',
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
  lodging: 'Alojamiento',
  other: 'Otro',
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
  lodging: 'mdi mdi-bed',
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

// reservas que son desplazamientos (cabecera azul en la agenda, día de salida)
export const TRANSPORT_TYPES: BookingType[] = ['flight', 'train', 'bus', 'ferry']

export function isTransport(type: BookingType): boolean {
  return TRANSPORT_TYPES.includes(type)
}

// MDI para lo que PrimeIcons no cubre bien (cama, avión, tren, ferry…)
export const BOOKING_TYPE_ICONS: Record<BookingType, string> = {
  hotel: 'mdi mdi-bed',
  flight: 'mdi mdi-airplane',
  train: 'mdi mdi-train',
  bus: 'mdi mdi-bus',
  ferry: 'mdi mdi-ferry',
  car_rental: 'mdi mdi-car',
  activity: 'mdi mdi-ticket-outline',
  other: 'mdi mdi-bookmark-outline',
}

// Monedas soportadas por frankfurter (BCE) más las habituales
export const CURRENCIES = [
  'EUR', 'USD', 'GBP', 'JPY', 'CHF', 'AUD', 'BGN', 'BRL', 'CAD', 'CNY',
  'CZK', 'DKK', 'HKD', 'HUF', 'IDR', 'ILS', 'INR', 'ISK', 'KRW', 'MXN',
  'MYR', 'NOK', 'NZD', 'PHP', 'PLN', 'RON', 'SEK', 'SGD', 'THB', 'TRY', 'ZAR',
]

export function toSelectOptions<T extends string>(labels: Record<T, string>) {
  return (Object.entries(labels) as [T, string][]).map(([value, label]) => ({ value, label }))
}
