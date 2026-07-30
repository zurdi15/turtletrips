import { describe, expect, it } from 'vitest'
import { extractResetToken, initials, safeRedirect, validatePassword } from './auth'

describe('initials', () => {
  it('toma la primera letra de las dos primeras palabras', () => {
    expect(initials('Ada Lovelace')).toBe('AL')
    expect(initials('zurdi')).toBe('Z')
    expect(initials('  maría   del mar ')).toBe('MD')
  })

  it('aguanta unicode y vacíos', () => {
    expect(initials('Ángela Ruiz')).toBe('ÁR')
    expect(initials('👩 viajera')).toBe('👩V')
    expect(initials('   ')).toBe('?')
  })
})

describe('validatePassword', () => {
  it('exige 8 caracteres y confirmación idéntica', () => {
    expect(validatePassword('corta', 'corta')).toBe('tooShort')
    expect(validatePassword('12345678', '87654321')).toBe('mismatch')
    expect(validatePassword('12345678', '12345678')).toBeNull()
  })
})

describe('extractResetToken', () => {
  it('saca el token de la URL entera o lo deja pasar pelado', () => {
    expect(extractResetToken('https://tt.casa/reset-password?token=ab-c_1')).toBe('ab-c_1')
    expect(extractResetToken('  /reset-password?foo=1&token=xyz#hash ')).toBe('xyz')
    expect(extractResetToken('ab-c_1')).toBe('ab-c_1')
    expect(extractResetToken('  ')).toBe('')
  })
})

describe('safeRedirect', () => {
  it('solo acepta rutas internas', () => {
    expect(safeRedirect('/trips/3')).toBe('/trips/3')
    expect(safeRedirect('//evil.com')).toBe('/')
    expect(safeRedirect('https://evil.com')).toBe('/')
    expect(safeRedirect(undefined)).toBe('/')
    expect(safeRedirect(['/a', '/b'])).toBe('/')
  })
})
