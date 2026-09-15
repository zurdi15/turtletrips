import { describe, expect, it } from 'vitest'
import type { LinkGroup, TripLink } from '../api/types'
import { bucketsFromLists, groupLinks, linkHost } from './links'

function group(id: number, position: number): LinkGroup {
  return { id, trip_id: 1, name: `G${id}`, icon: null, position }
}

function link(id: number, group_id: number | null, position: number): TripLink {
  return { id, trip_id: 1, group_id, title: `L${id}`, url: 'https://x.example', notes: null, position, image_url: null }
}

describe('groupLinks', () => {
  it('ordena bloques por posición y deja los sueltos al final', () => {
    const sections = groupLinks(
      [group(1, 1), group(2, 0)],
      [link(10, 1, 0), link(11, null, 0), link(12, 2, 1), link(13, 2, 0)],
    )
    expect(sections.map((s) => s.group?.id ?? null)).toEqual([2, 1, null])
    expect(sections[0]!.links.map((l) => l.id)).toEqual([13, 12])
    expect(sections[1]!.links.map((l) => l.id)).toEqual([10])
    expect(sections[2]!.links.map((l) => l.id)).toEqual([11])
  })

  it('un enlace de un bloque desconocido cae en "sin bloque"', () => {
    const sections = groupLinks([], [link(1, 99, 0)])
    expect(sections).toHaveLength(1)
    expect(sections[0]!.group).toBeNull()
    expect(sections[0]!.links.map((l) => l.id)).toEqual([1])
  })

  it('siempre hay sección "sin bloque", aunque esté vacía', () => {
    const sections = groupLinks([group(1, 0)], [])
    expect(sections.map((s) => s.group?.id ?? null)).toEqual([1, null])
  })
})

describe('bucketsFromLists', () => {
  it('traduce la clave "none" a null y conserva el orden', () => {
    expect(
      bucketsFromLists({
        '3': [link(1, 3, 0), link(2, 3, 1)],
        none: [link(4, null, 0)],
      }),
    ).toEqual([
      { group_id: 3, ids: [1, 2] },
      { group_id: null, ids: [4] },
    ])
  })
})

describe('linkHost', () => {
  it('quita esquema, www y ruta', () => {
    expect(linkHost('https://www.booking.com/hotel/kh/x.html')).toBe('booking.com')
  })
  it('devuelve la url tal cual si no parsea', () => {
    expect(linkHost('no es una url')).toBe('no es una url')
  })
})
