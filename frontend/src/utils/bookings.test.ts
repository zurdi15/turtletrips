import { describe, expect, it } from 'vitest'
import { bookingAddressLine } from './bookings'

describe('bookingAddressLine', () => {
  it('sin dirección no hay línea', () => {
    expect(bookingAddressLine(null, 'Hotel')).toBeNull()
    expect(bookingAddressLine('   ', 'Hotel')).toBeNull()
  })

  it('quita el nombre del lugar cuando repite el título', () => {
    expect(
      bookingAddressLine('La Siesta Hotel, 94 Mã Mây, Hoàn Kiếm, Hà Nội', 'la siesta hotel'),
    ).toBe('94 Mã Mây, Hoàn Kiếm, Hà Nội')
  })

  it('deja la dirección entera si el título es otro', () => {
    expect(bookingAddressLine('94 Mã Mây, Hoàn Kiếm, Hà Nội', 'Hotel en Hanoi')).toBe(
      '94 Mã Mây, Hoàn Kiếm, Hà Nội',
    )
  })

  it('una dirección de una sola parte igual al título se queda', () => {
    expect(bookingAddressLine('Hà Nội', 'Hà Nội')).toBe('Hà Nội')
  })
})
