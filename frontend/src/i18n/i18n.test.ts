import { describe, expect, it } from 'vitest'
import es from './es'
import en from './en'

function keyTree(obj: Record<string, unknown>, prefix = ''): string[] {
  return Object.entries(obj).flatMap(([key, value]) =>
    typeof value === 'object' && value !== null
      ? keyTree(value as Record<string, unknown>, `${prefix}${key}.`)
      : [`${prefix}${key}`],
  )
}

describe('árboles de mensajes', () => {
  it('es y en tienen exactamente las mismas claves', () => {
    expect(keyTree(en as never).sort()).toEqual(keyTree(es as never).sort())
  })

  it('ningún mensaje queda vacío', () => {
    const empty = (tree: Record<string, unknown>, lang: string) =>
      keyTree(tree)
        .filter((k) => {
          const value = k.split('.').reduce<unknown>((o, part) => (o as never)?.[part], tree)
          return typeof value === 'string' && value.trim() === ''
        })
        .map((k) => `${lang}:${k}`)
    expect([...empty(es as never, 'es'), ...empty(en as never, 'en')]).toEqual([])
  })
})
