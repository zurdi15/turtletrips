import { describe, expect, it } from 'vitest'
import { canFrame, clamp01, coverOverflow, dragFocus, focusStyle } from './imageFocus'

describe('coverOverflow', () => {
  it('una panorámica en un marco cuadrado solo sobra por los lados', () => {
    const over = coverOverflow({ width: 4000, height: 1000 }, { width: 300, height: 300 })
    // escala = 300/1000 = 0,3 → 1200 de ancho contra 300 de marco
    expect(over.width).toBe(900)
    expect(over.height).toBe(0)
  })

  it('un retrato en un marco apaisado solo sobra por arriba y abajo', () => {
    const over = coverOverflow({ width: 1000, height: 2000 }, { width: 400, height: 200 })
    expect(over.width).toBe(0)
    expect(over.height).toBe(600)
  })

  it('mismo aspecto que el marco: no sobra nada', () => {
    expect(coverOverflow({ width: 1600, height: 900 }, { width: 800, height: 450 })).toEqual({
      width: 0,
      height: 0,
    })
  })

  it('medidas imposibles no revientan ni dan NaN', () => {
    expect(coverOverflow({ width: 0, height: 0 }, { width: 10, height: 10 })).toEqual({
      width: 0,
      height: 0,
    })
  })
})

describe('dragFocus', () => {
  const overflow = { width: 200, height: 100 }

  it('arrastrar a la derecha destapa lo de la izquierda: el foco baja', () => {
    expect(dragFocus({ x: 0.5, y: 0.5 }, 50, 0, overflow).x).toBeCloseTo(0.25)
  })

  it('arrastrar hacia arriba sube el foco', () => {
    expect(dragFocus({ x: 0.5, y: 0.5 }, 0, -50, overflow).y).toBeCloseTo(1)
  })

  it('no se sale de la imagen por mucho que arrastres', () => {
    const far = dragFocus({ x: 0.5, y: 0.5 }, -5000, 5000, overflow)
    expect(far).toEqual({ x: 1, y: 0 })
  })

  it('un eje sin sobra no se mueve (si no, saltaría solo)', () => {
    const focus = { x: 0.3, y: 0.7 }
    expect(dragFocus(focus, 80, 80, { width: 0, height: 0 })).toEqual(focus)
  })
})

describe('focusStyle', () => {
  it('traduce a porcentajes de object-position', () => {
    expect(focusStyle(0, 1)).toBe('0% 100%')
    expect(focusStyle(0.25, 0.5)).toBe('25% 50%')
  })

  it('sin valor, centrada — como hacía el navegador antes de esto', () => {
    expect(focusStyle(null, undefined)).toBe('50% 50%')
  })

  it('redondea a una décima: nadie necesita 33,333333%', () => {
    expect(focusStyle(1 / 3, 2 / 3)).toBe('33.3% 66.7%')
  })
})

describe('clamp01 / canFrame', () => {
  it('clamp01 devuelve el centro ante un valor imposible', () => {
    expect(clamp01(NaN)).toBe(0.5)
    expect(clamp01(-3)).toBe(0)
    expect(clamp01(9)).toBe(1)
  })

  it('canFrame descarta las sobras de menos de un píxel (redondeos)', () => {
    expect(canFrame({ width: 0.4, height: 0.9 })).toBe(false)
    expect(canFrame({ width: 0, height: 40 })).toBe(true)
  })
})
