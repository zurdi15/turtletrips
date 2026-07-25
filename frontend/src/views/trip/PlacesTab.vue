<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import ClusterBtn from '../../components/ui/ClusterBtn.vue'
import PlaceMap from '../../components/PlaceMap.vue'
import PlaceFormDialog from '../../components/places/PlaceFormDialog.vue'
import PlaceCard from '../../components/places/PlaceCard.vue'
import EmptyState from '../../components/EmptyState.vue'
import TabSkeleton from '../../components/TabSkeleton.vue'
import type { Booking, Expense, Place, Trip } from '../../api/types'
import { PLACE_CATEGORY_LABELS, toSelectOptions } from '../../constants'
import { usePlacesStore } from '../../stores/places'
import { useBookingsStore } from '../../stores/bookings'
import { useExpensesStore } from '../../stores/expenses'
import { useCrudView } from '../../composables/useCrudView'
import { useTripTabData } from '../../composables/useTripTabData'

const props = defineProps<{ trip: Trip }>()
const store = usePlacesStore()
const bookings = useBookingsStore()
const expenses = useExpensesStore()

const selectedId = ref<number | null>(null)
const searchText = ref('')
const filterCategory = ref<string>('all')
const filterVisited = ref<'all' | 'pending' | 'visited'>('all')

// vista de la tab: lista, mapa a todo el ancho, o ambos lado a lado.
// En móvil arranca en lista (no cabe todo); en escritorio en ambos.
const panel = ref<'list' | 'both' | 'map'>('both')
const mapRef = ref<InstanceType<typeof PlaceMap> | null>(null)
const panelOptions = [
  { value: 'list', label: 'Lista', icon: 'pi pi-list' },
  { value: 'both', label: 'Ambos', icon: 'pi pi-objects-column' },
  { value: 'map', label: 'Mapa', icon: 'pi pi-map' },
] as const

watch(panel, async (value) => {
  if (value === 'list') return
  await nextTick()
  // Leaflet no conoce su tamaño si se montó oculto o cambia el ancho
  setTimeout(() => mapRef.value?.refresh(), 60)
})

const route = useRoute()

useTripTabData(() => props.trip, {
  load(tripId) {
    bookings.load(tripId)
    expenses.load(tripId)
    return store.load(tripId)
  },
  // llegar desde un gasto enlazado (?place=id) selecciona y centra ese sitio
  afterFirstLoad() {
    const fromQuery = Number(route.query.place)
    if (fromQuery) selectedId.value = fromQuery
  },
})

const categoryOptions = [
  { value: 'all', label: 'Todas las categorías' },
  ...toSelectOptions(PLACE_CATEGORY_LABELS),
]
// "Todos" en el centro, igual que "Ambos" en el selector de panel
const visitedOptions = [
  { value: 'pending', label: 'Pendientes', icon: 'pi pi-clock' },
  { value: 'all', label: 'Todos', icon: 'pi pi-asterisk' },
  { value: 'visited', label: 'Visitados', icon: 'pi pi-check-circle' },
] as const

// reservas enlazadas a cada sitio (chip → pestaña Reservas)
const bookingsByPlace = computed(() => {
  const map = new Map<number, Booking[]>()
  for (const b of bookings.items) {
    if (b.place_id != null) map.set(b.place_id, [...(map.get(b.place_id) ?? []), b])
  }
  return map
})

// gastos enlazados a cada sitio (chip → pestaña Gastos, con highlight)
const expensesByPlace = computed(() => {
  const map = new Map<number, Expense[]>()
  for (const e of expenses.items) {
    if (e.place_id != null) map.set(e.place_id, [...(map.get(e.place_id) ?? []), e])
  }
  return map
})

const filtered = computed(() =>
  store.items.filter((p) => {
    if (filterCategory.value !== 'all' && p.category !== filterCategory.value) return false
    if (filterVisited.value === 'pending' && p.visited) return false
    if (filterVisited.value === 'visited' && !p.visited) return false
    if (searchText.value && !p.name.toLowerCase().includes(searchText.value.toLowerCase()))
      return false
    return true
  }),
)

const {
  showForm,
  editing,
  openNew,
  openEdit,
  removeItem: removePlace,
} = useCrudView<Place>({
  confirm: (place) => ({ message: `¿Eliminar "${place.name}"?`, header: 'Eliminar sitio' }),
  remove: (place) => store.remove(place.id),
})
</script>

<template>
  <div>
    <!-- el DOM es el orden móvil; en desktop los sm:order-* lo recomponen en dos
         filas: acciones arriba y, justo encima del contenido, contador (izquierda)
         + selector de vista (derecha) -->
    <div class="flex flex-wrap items-center gap-2 mb-4">
      <Button
        label="Nuevo sitio"
        icon="pi pi-plus"
        class="w-full sm:w-auto sm:order-1"
        @click="openNew"
      />
      <InputText
        v-model="searchText"
        placeholder="Buscar…"
        class="flex-1 sm:flex-none sm:w-44 sm:order-2"
      />
      <!-- el selector de categoría absorbe el espacio sobrante: la fila queda completa -->
      <Select
        v-model="filterCategory"
        :options="categoryOptions"
        optionLabel="label"
        optionValue="value"
        class="flex-1 min-w-[10rem] sm:order-3"
      />
      <ClusterBtn
        v-model="filterVisited"
        :options="visitedOptions"
        class="max-sm:basis-full max-sm:w-full sm:order-4"
      />
      <ClusterBtn
        v-model="panel"
        :options="panelOptions"
        class="max-sm:basis-full max-sm:w-full sm:order-8"
      />
      <span class="hidden sm:block shrink-0 text-sm text-ink-faint sm:order-6">
        {{ store.items.filter((p) => p.visited).length }}/{{ store.items.length }} visitados
      </span>
      <span class="hidden sm:block flex-1 sm:order-7" />
      <!-- salto de fila entre acciones y vista; el -mt-2 compensa el doble row-gap -->
      <span class="hidden sm:block basis-full -mt-2 sm:order-5" />
    </div>

    <div class="grid grid-cols-1 gap-6" :class="panel === 'both' ? 'lg:grid-cols-2' : ''">
      <div
        class="tt-stagger flex-col gap-2 max-h-[70vh] lg:max-h-[600px] overflow-y-auto pr-1"
        :class="panel === 'map' ? 'hidden' : 'flex'"
      >
        <PlaceCard
          v-for="place in filtered"
          :key="place.id"
          :place="place"
          :tripId="trip.id"
          :bookings="bookingsByPlace.get(place.id) ?? []"
          :expenses="expensesByPlace.get(place.id) ?? []"
          :baseCurrency="trip.base_currency"
          :selected="selectedId === place.id"
          @select="selectedId = place.id"
          @edit="openEdit(place)"
          @remove="removePlace(place)"
          @toggle-visited="store.toggleVisited(place)"
        />
        <TabSkeleton
          v-if="store.loading && !store.items.length"
          variant="cards"
          :rows="4"
        />
        <EmptyState
          v-else-if="!store.items.length"
          icon="pi pi-map-marker"
          title="Sin sitios guardados"
          subtitle="Añade los sitios que quieres ver en este viaje"
        />
        <p v-else-if="!filtered.length" class="text-center text-sm text-ink-faint py-8">
          Ningún sitio coincide con los filtros
        </p>
      </div>

      <div
        class="h-[65vh] lg:h-[600px]"
        :class="[
          panel === 'list' ? 'hidden' : 'block',
          panel === 'both' ? 'lg:sticky lg:top-20' : '',
        ]"
      >
        <PlaceMap
          ref="mapRef"
          :places="filtered"
          :bookings="bookings.items"
          :selectedId="selectedId"
          :countryCode="trip.countries[0]"
          @select="(id) => (selectedId = id)"
        />
      </div>
    </div>

    <PlaceFormDialog v-model:visible="showForm" :place="editing" />
  </div>
</template>
