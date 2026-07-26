import { describe, expect, it } from 'vitest'
import { resolveDark } from './useTheme'

describe('resolveDark', () => {
  it('light y dark ignoran el sistema', () => {
    expect(resolveDark('light', true)).toBe(false)
    expect(resolveDark('dark', false)).toBe(true)
  })

  it('system sigue la preferencia del SO', () => {
    expect(resolveDark('system', true)).toBe(true)
    expect(resolveDark('system', false)).toBe(false)
  })
})
