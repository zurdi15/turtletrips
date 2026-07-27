import { onScopeDispose, ref, type Ref } from 'vue'

/** true mientras la media query casa; reactivo a rotaciones y resize */
export function useMediaQuery(query: string): Ref<boolean> {
  const mq = window.matchMedia(query)
  const matches = ref(mq.matches)
  const update = (e: MediaQueryListEvent) => (matches.value = e.matches)
  mq.addEventListener('change', update)
  onScopeDispose(() => mq.removeEventListener('change', update))
  return matches
}
