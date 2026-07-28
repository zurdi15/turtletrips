import type { BookingType, PlaceCategory, TripStatus } from './api/types'
import type { TransferMode } from './utils/transfers'

// Claves i18n (common.*) de los enums de la API; traducir con t(...KEYS[valor])
export const TRIP_STATUS_KEYS: Record<TripStatus, string> = {
  planning: 'common.tripStatus.planning',
  upcoming: 'common.tripStatus.upcoming',
  ongoing: 'common.tripStatus.ongoing',
  done: 'common.tripStatus.done',
}

export const TRIP_STATUS_SEVERITY: Record<TripStatus, string> = {
  planning: 'info',
  upcoming: 'success',
  ongoing: 'success',
  done: 'secondary',
}

export const PLACE_CATEGORY_KEYS: Record<PlaceCategory, string> = {
  city: 'common.placeCategory.city',
  town: 'common.placeCategory.town',
  sight: 'common.placeCategory.sight',
  food: 'common.placeCategory.food',
  museum: 'common.placeCategory.museum',
  nature: 'common.placeCategory.nature',
  viewpoint: 'common.placeCategory.viewpoint',
  shopping: 'common.placeCategory.shopping',
  lodging: 'common.placeCategory.lodging',
  other: 'common.placeCategory.other',
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

export const BOOKING_TYPE_KEYS: Record<BookingType, string> = {
  hotel: 'common.bookingType.hotel',
  flight: 'common.bookingType.flight',
  train: 'common.bookingType.train',
  bus: 'common.bookingType.bus',
  ferry: 'common.bookingType.ferry',
  car_rental: 'common.bookingType.car_rental',
  activity: 'common.bookingType.activity',
  other: 'common.bookingType.other',
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

// modo con el que se estiman los traslados entre paradas de un día
export const TRANSFER_MODE_KEYS: Record<TransferMode, string> = {
  walk: 'common.transferMode.walk',
  bike: 'common.transferMode.bike',
  transit: 'common.transferMode.transit',
  car: 'common.transferMode.car',
}

export const TRANSFER_MODE_ICONS: Record<TransferMode, string> = {
  walk: 'mdi mdi-walk',
  bike: 'mdi mdi-bike',
  transit: 'mdi mdi-bus',
  car: 'mdi mdi-car',
}

// Monedas soportadas por frankfurter (BCE) más las habituales
export const CURRENCIES = [
  'EUR', 'USD', 'GBP', 'JPY', 'CHF', 'AUD', 'BGN', 'BRL', 'CAD', 'CNY',
  'CZK', 'DKK', 'HKD', 'HUF', 'IDR', 'ILS', 'INR', 'ISK', 'KRW', 'MXN',
  'MYR', 'NOK', 'NZD', 'PHP', 'PLN', 'RON', 'SEK', 'SGD', 'THB', 'TRY', 'ZAR',
]

/** Opciones para selects a partir de un mapa de claves i18n (t traduce el label) */
export function toSelectOptions<T extends string>(
  keys: Record<T, string>,
  t: (key: string) => string,
) {
  return (Object.entries(keys) as [T, string][]).map(([value, key]) => ({ value, label: t(key) }))
}
