import { ref, type Ref } from 'vue'
import { api } from '../api/client'

interface HasId {
  id: number
}

export interface GlobalResourceOptions<T> {
  listPath: string
  itemPath: (id: number) => string
  /** orden estable tras crear (p. ej. viajeros por nombre) */
  sort?: (a: T, b: T) => number
}

/**
 * Base de los recursos globales (no anidados en un viaje) con cache de carga:
 * estado { items, loaded } + load(force)/create/update/remove. El análogo de
 * useTripResource para /travelers y /categories.
 */
export function useGlobalResource<T extends HasId, TCreate, TUpdate>(
  opts: GlobalResourceOptions<T>,
) {
  const items = ref<T[]>([]) as Ref<T[]>
  const loaded = ref(false)

  async function load(force = false) {
    if (loaded.value && !force) return
    items.value = await api.get<T[]>(opts.listPath)
    loaded.value = true
  }

  async function create(payload: TCreate): Promise<T> {
    const item = await api.post<T>(opts.listPath.split('?')[0], payload)
    if (!items.value.some((i) => i.id === item.id)) {
      items.value.push(item)
      if (opts.sort) items.value.sort(opts.sort)
    }
    return item
  }

  async function update(id: number, payload: TUpdate): Promise<T> {
    const item = await api.patch<T>(opts.itemPath(id), payload)
    const idx = items.value.findIndex((i) => i.id === id)
    if (idx >= 0) items.value[idx] = item
    return item
  }

  async function remove(id: number) {
    await api.delete(opts.itemPath(id))
    items.value = items.value.filter((i) => i.id !== id)
  }

  return { items, loaded, load, create, update, remove }
}
