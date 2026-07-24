import { ref, type Ref } from 'vue'
import { api } from '../api/client'

interface HasId {
  id: number
}

export interface TripResourceOptions {
  listPath: (tripId: number) => string
  itemPath: (id: number) => string
  /** dónde insertar los creados (expenses lista descendente → unshift) */
  insert?: 'push' | 'unshift'
}

/**
 * Base compartida de los stores de recursos anidados en un viaje:
 * estado { items, tripId, loading } + acciones load/create/update/remove.
 * Cada store la compone y añade sus extras.
 */
export function useTripResource<T extends HasId, TInput>(opts: TripResourceOptions) {
  const items = ref<T[]>([]) as Ref<T[]>
  const tripId = ref<number | null>(null)
  const loading = ref(false)

  async function load(id: number) {
    loading.value = true
    tripId.value = id
    try {
      items.value = await api.get<T[]>(opts.listPath(id))
    } finally {
      loading.value = false
    }
  }

  async function create(payload: TInput): Promise<T> {
    const item = await api.post<T>(opts.listPath(tripId.value as number), payload)
    if (opts.insert === 'unshift') items.value.unshift(item)
    else items.value.push(item)
    return item
  }

  async function update(id: number, payload: TInput): Promise<T> {
    const item = await api.patch<T>(opts.itemPath(id), payload)
    const idx = items.value.findIndex((i) => i.id === id)
    if (idx >= 0) items.value[idx] = item
    return item
  }

  async function remove(id: number) {
    await api.delete(opts.itemPath(id))
    items.value = items.value.filter((i) => i.id !== id)
  }

  return { items, tripId, loading, load, create, update, remove }
}
