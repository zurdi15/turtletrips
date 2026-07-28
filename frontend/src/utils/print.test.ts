import { describe, expect, it } from 'vitest'
import { printDocumentTitle, printSections, resolvePrintOptions } from './print'
import type { PrintContent } from './print'

const FULL: PrintContent = {
  days: 12,
  places: 20,
  locatedPlaces: 20,
  bookings: 10,
  hasExpenses: true,
}

describe('resolvePrintOptions', () => {
  it('por defecto se imprime todo', () => {
    expect(resolvePrintOptions({}, { allowExpenses: true })).toEqual({
      layout: 'report',
      map: true,
      notes: true,
      expenses: true,
    })
  })

  it('la query apaga secciones', () => {
    const options = resolvePrintOptions({ map: '0', notes: '0' }, { allowExpenses: true })
    expect(options).toMatchObject({ map: false, notes: false, expenses: true })
  })

  it('sin permiso NO hay gastos, aunque los pidan por la URL', () => {
    const options = resolvePrintOptions({ expenses: '1' }, { allowExpenses: false })
    expect(options.expenses).toBe(false)
  })

  it('acepta el layout de álbum (fase 7) y cae a informe con cualquier otra cosa', () => {
    expect(resolvePrintOptions({ layout: 'album' }, { allowExpenses: true }).layout).toBe('album')
    expect(resolvePrintOptions({ layout: 'raro' }, { allowExpenses: true }).layout).toBe('report')
  })
})

describe('printSections', () => {
  const options = resolvePrintOptions({}, { allowExpenses: true })

  it('orden fijo con todo el contenido', () => {
    expect(printSections(options, FULL)).toEqual([
      'cover',
      'itinerary',
      'map',
      'places',
      'bookings',
      'expenses',
    ])
  })

  it('la portada siempre está, aunque el viaje esté vacío', () => {
    expect(
      printSections(options, { days: 0, places: 0, locatedPlaces: 0, bookings: 0, hasExpenses: false }),
    ).toEqual(['cover'])
  })

  it('sitios sin coordenadas: lista sí, mapa no', () => {
    expect(printSections(options, { ...FULL, locatedPlaces: 0 })).not.toContain('map')
    expect(printSections(options, { ...FULL, locatedPlaces: 0 })).toContain('places')
  })

  it('apagar el mapa no se lleva por delante la lista de sitios', () => {
    const sections = printSections({ ...options, map: false }, FULL)
    expect(sections).not.toContain('map')
    expect(sections).toContain('places')
  })

  it('sin gastos que enseñar no aparece la sección', () => {
    expect(printSections(options, { ...FULL, hasExpenses: false })).not.toContain('expenses')
    expect(printSections({ ...options, expenses: false }, FULL)).not.toContain('expenses')
  })
})

describe('printDocumentTitle', () => {
  it('el nombre del PDF lleva la fecha de salida', () => {
    expect(printDocumentTitle('Japón 2026', '2026-02-07')).toBe('Japón 2026 — 2026-02-07')
    expect(printDocumentTitle('Japón 2026', null)).toBe('Japón 2026')
  })
})
