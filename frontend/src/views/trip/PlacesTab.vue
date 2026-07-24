<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import SelectButton from 'primevue/selectbutton'
import Tag from 'primevue/tag'
import { useConfirm } from 'primevue/useconfirm'
import PlaceMap from '../../components/PlaceMap.vue'
import PlaceFormDialog from '../../components/PlaceFormDialog.vue'
import EmptyState from '../../components/EmptyState.vue'
import TabSkeleton from '../../components/TabSkeleton.vue'
import type { Booking, Expense, Place, Trip } from '../../api/types'
import {
  PLACE_CATEGORY_COLORS,
  PLACE_CATEGORY_ICONS,
  PLACE_CATEGORY_LABELS,
  toSelectOptions,
} from '../../constants'
import { usePlacesStore } from '../../stores/places'
import { useBookingsStore } from '../../stores/bookings'
import { useExpensesStore } from '../../stores/expenses'
import { formatMoney } from '../../composables/useMoney'

const props = defineProps<{ trip: Trip }>()
const store = usePlacesStore()
const bookings = useBookingsStore()
const expenses = useExpensesStore()
const confirm = useConfirm()

const showForm = ref(false)
const editing = ref<Place | null>(null)
const selectedId = ref<number | null>(null)
const searchText = ref('')
const filterCategory = ref<string>('all')
const filterVisited = ref<'all' | 'pending' | 'visited'>('all')

// vista de la tab: lista, mapa a todo el ancho, o ambos lado a lado.
// En móvil arranca en lista (no cabe todo); en escritorio en ambos.
const panel = ref<'list' | 'both' | 'map'>(window.innerWidth < 1024 ? 'list' : 'both')
const mapRef = ref<InstanceType<typeof PlaceMap> | null>(null)
const panelOptions = [
  { value: 'list', label: 'Lista', icon: 'pi pi-list' },
  { value: 'both', label: 'Ambos', icon: 'pi pi-objects-column' },
  { value: 'map', label: 'Mapa', icon: 'pi pi-map' },
]

watch(panel, async (value) => {
  if (value === 'list') return
  await nextTick()
  // Leaflet no conoce su tamaño si se montó oculto o cambia el ancho
  setTimeout(() => mapRef.value?.refresh(), 60)
})

const route = useRoute()

onMounted(async () => {
  bookings.load(props.trip.id)
  expenses.load(props.trip.id)
  await store.load(props.trip.id)
  // llegar desde un gasto enlazado (?place=id) selecciona y centra ese sitio
  const fromQuery = Number(route.query.place)
  if (fromQuery) selectedId.value = fromQuery
})
watch(() => props.trip.id, (id) => {
  store.load(id)
  bookings.load(id)
  expenses.load(id)
})

const categoryOptions = [
  { value: 'all', label: 'Todas las categorías' },
  ...toSelectOptions(PLACE_CATEGORY_LABELS),
]
const visitedOptions = [
  { value: 'all', label: 'Todos' },
  { value: 'pending', label: 'Pendientes' },
  { value: 'visited', label: 'Visitados' },
]

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

function openNew() {
  editing.value = null
  showForm.value = true
}
function openEdit(place: Place) {
  editing.value = place
  showForm.value = true
}
function removePlace(place: Place) {
  confirm.require({
    message: `¿Eliminar "${place.name}"?`,
    header: 'Eliminar sitio',
    icon: 'pi pi-exclamation-triangle',
    rejectProps: { label: 'Cancelar', severity: 'secondary', outlined: true },
    acceptProps: { label: 'Eliminar', severity: 'danger' },
    accept: () => store.remove(place.id),
  })
}
</script>

<template>
  <div>
    <div class="flex flex-wrap items-center gap-2 mb-4">
      <Button label="Nuevo sitio" icon="pi pi-plus" @click="openNew" />
      <InputText v-model="searchText" placeholder="Buscar…" class="flex-1 sm:flex-none sm:w-44" />
      <!-- el selector de categoría absorbe el espacio sobrante: la fila queda completa -->
      <Select
        v-model="filterCategory"
        :options="categoryOptions"
        optionLabel="label"
        optionValue="value"
        class="flex-1 min-w-[10rem]"
      />
      <SelectButton
        v-model="filterVisited"
        :options="visitedOptions"
        optionLabel="label"
        optionValue="value"
        :allowEmpty="false"
      />
      <SelectButton
        v-model="panel"
        :options="panelOptions"
        optionLabel="label"
        optionValue="value"
        :allowEmpty="false"
      />
      <span class="shrink-0 text-sm text-slate-400 hidden sm:block">
        {{ store.items.filter((p) => p.visited).length }}/{{ store.items.length }} visitados
      </span>
    </div>

    <div class="grid grid-cols-1 gap-6" :class="panel === 'both' ? 'lg:grid-cols-2' : ''">
      <div
        class="tt-stagger flex-col gap-2 max-h-[70vh] lg:max-h-[600px] overflow-y-auto pr-1"
        :class="panel === 'map' ? 'hidden' : 'flex'"
      >
        <div
          v-for="place in filtered"
          :key="place.id"
          class="tt-lift bg-white rounded-xl border p-3 cursor-pointer"
          :class="
            selectedId === place.id
              ? 'border-[var(--p-primary-color)] ring-1 ring-[var(--p-primary-color)]'
              : 'border-slate-200 hover:border-slate-300'
          "
          @click="selectedId = place.id"
        >
          <div class="flex items-start gap-3">
            <!-- visitado: anillo verde en el icono (sin tachar el nombre) -->
            <span
              class="w-9 h-9 rounded-full flex items-center justify-center shrink-0 text-white"
              :class="{ 'ring-2 ring-emerald-400': place.visited }"
              :style="{ background: PLACE_CATEGORY_COLORS[place.category] }"
            >
              <i :class="PLACE_CATEGORY_ICONS[place.category]" class="text-sm" />
            </span>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 flex-wrap">
                <span class="font-medium">{{ place.name }}</span>
                <i
                  v-if="place.priority > 0"
                  class="pi pi-star-fill text-amber-400 text-xs"
                  v-tooltip.top="'Imprescindible'"
                />
                <Tag
                  :value="PLACE_CATEGORY_LABELS[place.category]"
                  :style="{
                    background: `${PLACE_CATEGORY_COLORS[place.category]}20`,
                    color: PLACE_CATEGORY_COLORS[place.category],
                  }"
                  class="text-xs"
                />
                <!-- enlaces compactos a reserva y gasto: solo icono + tooltip -->
                <router-link
                  v-for="b in bookingsByPlace.get(place.id) ?? []"
                  :key="`bk-${b.id}`"
                  :to="{ name: 'trip-bookings', params: { id: trip.id }, query: { booking: b.id } }"
                  class="text-violet-600 no-underline"
                  v-tooltip.top="`Reserva: ${b.title}`"
                  @click.stop
                >
                  <i class="pi pi-ticket text-xs" />
                </router-link>
                <router-link
                  v-for="e in expensesByPlace.get(place.id) ?? []"
                  :key="`ex-${e.id}`"
                  :to="{ name: 'trip-expenses', params: { id: trip.id }, query: { expense: e.id } }"
                  class="text-amber-600 no-underline"
                  v-tooltip.top="`Gasto: ${e.description} · ${formatMoney(e.amount_base, trip.base_currency)}`"
                  @click.stop
                >
                  <i class="pi pi-wallet text-xs" />
                </router-link>
              </div>
              <p v-if="place.notes" class="text-sm text-slate-500 mt-0.5 truncate">{{ place.notes }}</p>
              <a
                v-if="place.url"
                :href="place.url"
                target="_blank"
                rel="noopener"
                class="text-xs text-sky-600 hover:underline"
                @click.stop
              >
                <i class="pi pi-external-link text-[10px]" /> enlace
              </a>
            </div>
            <div class="flex gap-1 shrink-0">
              <Button
                :icon="place.visited ? 'pi pi-check-circle' : 'pi pi-circle'"
                :severity="place.visited ? 'success' : 'secondary'"
                text
                size="small"
                v-tooltip.top="place.visited ? 'Marcar pendiente' : 'Marcar visitado'"
                @click.stop="store.toggleVisited(place)"
              />
              <Button icon="pi pi-pencil" text size="small" severity="secondary" @click.stop="openEdit(place)" />
              <Button icon="pi pi-trash" text size="small" severity="danger" @click.stop="removePlace(place)" />
            </div>
          </div>
        </div>
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
        <p v-else-if="!filtered.length" class="text-center text-sm text-slate-400 py-8">
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
