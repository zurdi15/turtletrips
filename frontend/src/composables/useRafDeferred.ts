import { computed, ref, watch, type ComputedRef, type Ref } from 'vue'

/**
 * Valor que sigue a `source` con dos frames de retraso: el frame actual pinta
 * lo barato (nav, skeleton) y el contenido pesado se monta después, evitando
 * congelar la transición. `pending` es true mientras el valor va por detrás.
 */
export function useRafDeferred<T>(source: () => T): {
  deferred: Ref<T>
  pending: ComputedRef<boolean>
} {
  const deferred = ref(source()) as Ref<T>
  watch(source, (value) => {
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        deferred.value = value
      })
    })
  })
  const pending = computed(() => deferred.value !== source())
  return { deferred, pending }
}
