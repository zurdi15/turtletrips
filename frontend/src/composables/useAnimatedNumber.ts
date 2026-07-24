import { onScopeDispose, ref, watch, type Ref } from 'vue'

/**
 * Valor numérico que persigue a su fuente con un tween (count-up).
 * La primera vez cuenta desde 0; los cambios posteriores parten del valor
 * mostrado. Con la fuente a null (sin dato) se refleja null al instante.
 * Sin requestAnimationFrame (tests/node) salta directo al objetivo.
 */
export function useAnimatedNumber(
  source: () => number | null | undefined,
  options: { duration?: number } = {},
): Ref<number | null> {
  const duration = options.duration ?? 550
  const display = ref<number | null>(null)

  const raf =
    typeof requestAnimationFrame === 'function' ? requestAnimationFrame.bind(globalThis) : null
  const caf =
    typeof cancelAnimationFrame === 'function'
      ? cancelAnimationFrame.bind(globalThis)
      : () => undefined
  let frame = 0

  function animate(from: number, to: number) {
    if (!raf || duration <= 0) {
      display.value = to
      return
    }
    const start = performance.now()
    const step = (now: number) => {
      const t = Math.min(1, (now - start) / duration)
      const eased = 1 - Math.pow(1 - t, 3) // easeOutCubic
      display.value = t < 1 ? from + (to - from) * eased : to
      if (t < 1) frame = raf(step)
    }
    frame = raf(step)
  }

  watch(
    source,
    (target) => {
      caf(frame)
      if (target == null) {
        display.value = null
        return
      }
      const from = display.value ?? 0
      if (from === target) {
        display.value = target
        return
      }
      animate(from, target)
    },
    { immediate: true },
  )

  onScopeDispose(() => caf(frame))
  return display
}
