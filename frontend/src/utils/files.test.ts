import { describe, expect, it } from 'vitest'
import { fileExtension, fileIcon, formatSize } from './files'

describe('fileIcon', () => {
  it('distingue pdf, imagen y genérico', () => {
    expect(fileIcon('application/pdf')).toContain('pi-file-pdf')
    expect(fileIcon('image/png')).toContain('pi-image')
    expect(fileIcon('image/jpeg')).toContain('pi-image')
    expect(fileIcon('text/plain')).toContain('pi-file')
  })
})

describe('formatSize', () => {
  it('bytes por debajo de 1 KB', () => {
    expect(formatSize(0)).toBe('0 B')
    expect(formatSize(1023)).toBe('1023 B')
  })
  it('kilobytes sin decimales', () => {
    expect(formatSize(1024)).toBe('1 KB')
    expect(formatSize(150 * 1024)).toBe('150 KB')
  })
  it('megabytes con un decimal', () => {
    expect(formatSize(1024 * 1024)).toBe('1.0 MB')
    expect(formatSize(2.5 * 1024 * 1024)).toBe('2.5 MB')
  })
})

describe('fileExtension', () => {
  it('devuelve la extensión con el punto', () => {
    expect(fileExtension('reserva.pdf')).toBe('.pdf')
    expect(fileExtension('foto.viaje.JPG')).toBe('.JPG')
  })

  it('sin extensión, cadena vacía (ni ocultos ni puntos finales)', () => {
    expect(fileExtension('billete')).toBe('')
    expect(fileExtension('.gitignore')).toBe('')
    expect(fileExtension('acaba en punto.')).toBe('')
  })
})
