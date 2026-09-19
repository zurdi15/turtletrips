/**
 * Dirección de una reserva para su tarjeta. La del geocoder (display_name)
 * empieza por el nombre del lugar, que el formulario copia al título: esa
 * primera parte se cae si repite el título, para no leerlo dos veces.
 */
export function bookingAddressLine(address: string | null, title: string): string | null {
  const text = address?.trim()
  if (!text) return null
  const [head, ...rest] = text.split(',')
  if (rest.length && head.trim().toLocaleLowerCase() === title.trim().toLocaleLowerCase()) {
    return rest.join(',').trim() || null
  }
  return text
}
