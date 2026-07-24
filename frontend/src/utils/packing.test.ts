import { describe, expect, it } from 'vitest'
import { groupPackingItems } from './packing'

const colorOf = (name: string) => (name === 'Ropa' ? '#f59e0b' : null)

describe('groupPackingItems', () => {
  it('respeta el orden de categorías conocidas y omite grupos vacíos', () => {
    const groups = groupPackingItems(
      [
        { category: 'Aseo', name: 'cepillo' },
        { category: 'Ropa', name: 'camiseta' },
      ],
      ['Ropa', 'Aseo', 'Tecnología'],
      colorOf,
    )
    expect(groups.map((g) => g.name)).toEqual(['Ropa', 'Aseo'])
    expect(groups[0].color).toBe('#f59e0b')
    expect(groups[1].color).toBeNull()
  })

  it('las categorías huérfanas (borradas de ajustes) van al final', () => {
    const groups = groupPackingItems(
      [
        { category: 'Buceo', name: 'gafas' },
        { category: 'Ropa', name: 'camiseta' },
        { category: 'Buceo', name: 'aletas' },
      ],
      ['Ropa'],
      colorOf,
    )
    expect(groups.map((g) => g.name)).toEqual(['Ropa', 'Buceo'])
    expect(groups[1].items).toHaveLength(2)
  })

  it('sin items: sin grupos', () => {
    expect(groupPackingItems([], ['Ropa'], colorOf)).toEqual([])
  })
})
