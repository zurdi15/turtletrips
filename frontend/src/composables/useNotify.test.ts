import { describe, expect, it } from 'vitest'
import { errorDetail } from './useNotify'
import { ApiError } from '../api/client'

describe('errorDetail', () => {
  it('ApiError: usa el detail formateado sin prefijo "Error:"', () => {
    const err = new ApiError(422, 'body.amount: value is not a valid float')
    expect(errorDetail(err)).toBe('body.amount: value is not a valid float')
  })
  it('Error genérico: message', () => {
    expect(errorDetail(new Error('falló la red'))).toBe('falló la red')
  })
  it('no-Error: String()', () => {
    expect(errorDetail('texto plano')).toBe('texto plano')
    expect(errorDetail(42)).toBe('42')
  })
  it('null/undefined: sin detalle', () => {
    expect(errorDetail(null)).toBeUndefined()
    expect(errorDetail(undefined)).toBeUndefined()
  })
})
