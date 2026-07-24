import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { effectScope, nextTick, ref, type EffectScope } from 'vue'
import { useAnimatedNumber } from './useAnimatedNumber'

let callbacks: FrameRequestCallback[]
let now: number
let scope: EffectScope

function pump(ms: number) {
  now += ms
  const batch = callbacks
  callbacks = []
  for (const cb of batch) cb(now)
}

beforeEach(() => {
  callbacks = []
  now = 0
  vi.stubGlobal('requestAnimationFrame', (cb: FrameRequestCallback) => {
    callbacks.push(cb)
    return callbacks.length
  })
  vi.stubGlobal('cancelAnimationFrame', () => undefined)
  vi.stubGlobal('performance', { now: () => now })
  scope = effectScope()
})

afterEach(() => {
  scope.stop()
  vi.unstubAllGlobals()
})

describe('useAnimatedNumber', () => {
  it('cuenta desde 0 hasta el objetivo y termina exacto', () => {
    const display = scope.run(() => useAnimatedNumber(() => 100, { duration: 500 }))!
    pump(0) // primer frame: t=0
    expect(display.value).toBe(0)
    pump(250) // mitad del tween: entre 0 y 100, easing por delante de lo lineal
    expect(display.value).toBeGreaterThan(50)
    expect(display.value).toBeLessThan(100)
    pump(250)
    expect(display.value).toBe(100)
    expect(callbacks.length).toBe(0) // no quedan frames pendientes
  })

  it('un cambio a mitad de camino parte del valor mostrado', async () => {
    const target = ref<number>(100)
    const display = scope.run(() =>
      useAnimatedNumber(() => target.value, { duration: 500 }),
    )!
    pump(0)
    pump(500)
    expect(display.value).toBe(100)

    target.value = 40
    await nextTick()
    pump(0)
    expect(display.value).toBe(100) // arranca desde 100, no desde 0
    pump(500)
    expect(display.value).toBe(40)
  })

  it('null se refleja al instante y al volver un número cuenta desde 0', async () => {
    const target = ref<number | null>(null)
    const display = scope.run(() =>
      useAnimatedNumber(() => target.value, { duration: 500 }),
    )!
    expect(display.value).toBeNull()

    target.value = 60
    await nextTick()
    pump(0)
    expect(display.value).toBe(0)
    pump(500)
    expect(display.value).toBe(60)

    target.value = null
    await nextTick()
    expect(display.value).toBeNull()
  })

  it('sin requestAnimationFrame salta directo al objetivo', () => {
    vi.unstubAllGlobals()
    const display = scope.run(() => useAnimatedNumber(() => 42))!
    expect(display.value).toBe(42)
  })
})
