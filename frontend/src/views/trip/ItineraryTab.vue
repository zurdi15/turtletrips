<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import Button from 'primevue/button'
import SelectButton from 'primevue/selectbutton'
import draggable from 'vuedraggable'
import ItineraryFormDialog from '../../components/itinerary/ItineraryFormDialog.vue'
import CalendarSubscribeDialog from '../../components/itinerary/CalendarSubscribeDialog.vue'
import EmptyState from '../../components/EmptyState.vue'
import TabSkeleton from '../../components/TabSkeleton.vue'
import ItineraryCalendar from '../../components/itinerary/ItineraryCalendar.vue'
import AgendaBookingSection, {
  type AgendaRow,
} from '../../components/itinerary/AgendaBookingSection.vue'
import AgendaItemRow from '../../components/itinerary/AgendaItemRow.vue'
import { API_BASE } from '../../api/client'
import type { ItineraryItem, Trip } from '../../api/types'
import { useItineraryStore } from '../../stores/itinerary'
import { usePlacesStore } from '../../stores/places'
import { useBookingsStore } from '../../stores/bookings'
import { useExpensesStore } from '../../stores/expenses'
import { useCrudView } from '../../composables/useCrudView'
import { useTripTabData } from '../../composables/useTripTabData'
import { expenseIdByBooking } from '../../utils/expenses'
import {
  agendaDayLabel,
  agendaDays,
  bookingHead,
  buildContinuations,
  buildLodgingByDay,
  buildOtherBookingsByDay,
  buildTransportsByDay,
  lodgingHead,
  transportHead,
  transportLabel,
} from '../../utils/itinerary'

const props = defineProps<{ trip: Trip }>()
const store = useItineraryStore()
const places = usePlacesStore()
const bookings = useBookingsStore()
const expenses = useExpensesStore()

const view = ref<'agenda' | 'calendar'>('agenda')
const viewOptions = [
  { value: 'agenda', label: 'Agenda', icon: 'pi pi-list' },
  { value: 'calendar', label: 'Calendario', icon: 'pi pi-calendar' },
]

const showSubscribe = ref(false)
const presetDay = ref<string | null>(null)

const icsUrl = computed(() => `${API_BASE}/trips/${props.trip.id}/calendar.ics`)

useTripTabData(() => props.trip, {
  load(tripId) {
    store.load(tripId)
    places.load(tripId)
    bookings.load(tripId)
    expenses.load(tripId)
  },
})

// ---- Agenda (derivación pura en utils/itinerary.ts) ----

// gasto generado por cada reserva (enlace directo con highlight)
const expenseByBooking = computed(() => expenseIdByBooking(expenses.items))

const transportsByDay = computed(() => buildTransportsByDay(bookings.items))
const otherBookingsByDay = computed(() => buildOtherBookingsByDay(bookings.items))
const lodgingByDay = computed(() => buildLodgingByDay(bookings.items))

const days = computed(() =>
  agendaDays(
    props.trip,
    store.items,
    transportsByDay.value,
    otherBookingsByDay.value,
    lodgingByDay.value,
  ),
)

const continuations = computed(() => buildContinuations(store.items))

const lists = reactive<Record<string, ItineraryItem[]>>({})

watch(
  [() => store.items, days],
  () => {
    for (const key of Object.keys(lists)) delete lists[key]
    for (const day of days.value) {
      lists[day] = (store.byDay.get(day) ?? []).slice()
    }
  },
  { immediate: true, deep: true },
)

function persistOrder() {
  const entries: { id: number; day: string; order_index: number }[] = []
  for (const [day, items] of Object.entries(lists)) {
    items.forEach((item, idx) => entries.push({ id: item.id, day, order_index: idx }))
  }
  store.reorder(entries)
}

function dayLabel(iso: string): { title: string; sub: string } {
  return agendaDayLabel(iso, props.trip.start_date)
}

function placeName(id: number | null): string | null {
  return id == null ? null : (places.items.find((p) => p.id === id)?.name ?? null)
}
function bookingTitle(id: number | null): string | null {
  return id == null ? null : (bookings.items.find((b) => b.id === id)?.title ?? null)
}

// filas de las tres bandas de reservas, ya etiquetadas para AgendaBookingSection
function transportRows(day: string): AgendaRow[] {
  return (transportsByDay.value.get(day) ?? []).map((e) => ({
    key: `t-${e.b.id}-${e.arrival ? 'a' : 's'}`,
    head: transportHead(e),
    label: transportLabel(e),
    bookingId: e.b.id,
    placeId: e.b.place_id,
    expenseId: expenseByBooking.value.get(e.b.id) ?? null,
  }))
}

function otherBookingRows(day: string): AgendaRow[] {
  return (otherBookingsByDay.value.get(day) ?? []).map((b) => ({
    key: `o-${b.id}`,
    head: bookingHead(b),
    label: b.title,
    bookingId: b.id,
    placeId: b.place_id,
    expenseId: expenseByBooking.value.get(b.id) ?? null,
    expenseInherit: true,
  }))
}

function lodgingRows(day: string): AgendaRow[] {
  return (lodgingByDay.value.get(day) ?? []).map((b) => ({
    key: `l-${b.id}`,
    head: lodgingHead(b, day),
    label: b.title,
    bookingId: b.id,
    placeId: b.place_id,
    expenseId: expenseByBooking.value.get(b.id) ?? null,
  }))
}

const crud = useCrudView<ItineraryItem>({
  confirm: (item) => ({
    message: `¿Eliminar "${item.title}" del itinerario?`,
    header: 'Eliminar actividad',
  }),
  remove: (item) => store.remove(item.id),
})
const { showForm, editing, openEdit, removeItem } = crud

function openNew(day?: string) {
  presetDay.value = day ?? null
  crud.openNew()
}

</script>

<template>
  <div>
    <div class="flex flex-wrap items-center gap-2 mb-4">
      <Button label="Nueva actividad" icon="pi pi-plus" class="w-full sm:w-auto" @click="openNew()" />
      <span class="hidden sm:block flex-1" />
      <SelectButton
        v-model="view"
        :options="viewOptions"
        optionLabel="label"
        optionValue="value"
        :allowEmpty="false"
        class="flex-1 sm:flex-none max-sm:[&_.p-togglebutton]:flex-1"
      />
      <a :href="icsUrl" download>
        <Button
          label="Exportar"
          icon="pi pi-calendar-plus"
          severity="secondary"
          outlined
          v-tooltip.bottom="'Descargar calendario (.ics)'"
          class="max-sm:[&_.p-button-label]:hidden max-sm:!w-10 max-sm:!h-10 max-sm:!p-0"
        />
      </a>
      <Button
        label="Suscribirse"
        icon="mdi mdi-calendar-sync"
        severity="secondary"
        outlined
        v-tooltip.bottom="'URL de suscripción: tu calendario se actualiza solo'"
        class="max-sm:[&_.p-button-label]:hidden max-sm:!w-10 max-sm:!h-10 max-sm:!p-0"
        @click="showSubscribe = true"
      />
    </div>

    <TabSkeleton
      v-if="store.loading && !store.items.length && !days.length"
      variant="cards"
      :rows="3"
    />

    <EmptyState
      v-else-if="!store.loading && !store.items.length && !days.length"
      icon="pi pi-calendar"
      title="Sin itinerario"
      subtitle="Define las fechas del viaje o añade una actividad para empezar"
    >
      <Button label="Nueva actividad" icon="pi pi-plus" @click="openNew()" />
    </EmptyState>

    <div v-else-if="view === 'agenda'" class="tt-stagger flex flex-col gap-4">
      <div
        v-for="day in days"
        :key="day"
        class="bg-surface rounded-card border border-line overflow-hidden"
      >
        <div class="flex items-center justify-between px-4 py-2.5 bg-surface-muted border-b border-line-subtle">
          <div class="flex items-baseline gap-2">
            <span class="font-semibold text-ink">{{ dayLabel(day).title }}</span>
            <span class="text-sm text-ink-faint capitalize">{{ dayLabel(day).sub }}</span>
          </div>
          <Button
            icon="pi pi-plus"
            text
            size="small"
            severity="secondary"
            v-tooltip.left="'Añadir a este día'"
            @click="openNew(day)"
          />
        </div>
        <!-- transportes del día: sección propia con cabecera -->
        <AgendaBookingSection
          v-if="transportRows(day).length"
          tone="info"
          title="Transporte"
          icon="mdi mdi-plane-train"
          :tripId="trip.id"
          :rows="transportRows(day)"
        />

        <!-- otras reservas del día (actividades, coche…) -->
        <AgendaBookingSection
          v-if="otherBookingRows(day).length"
          tone="warn"
          title="Reservas"
          icon="mdi mdi-ticket-outline"
          :tripId="trip.id"
          :rows="otherBookingRows(day)"
        />

        <draggable
          :list="lists[day]"
          group="itinerary"
          item-key="id"
          handle=".drag-handle"
          class="min-h-[2.5rem]"
          @end="persistOrder"
        >
          <template #item="{ element }">
            <AgendaItemRow
              :item="element"
              :tripId="trip.id"
              :placeName="placeName(element.place_id)"
              :bookingTitle="bookingTitle(element.booking_id)"
              :expenseId="element.booking_id ? (expenseByBooking.get(element.booking_id) ?? null) : null"
              @edit="openEdit(element)"
              @remove="removeItem(element)"
            />
          </template>
        </draggable>
        <div
          v-for="cont in continuations.get(day) ?? []"
          :key="`cont-${cont.id}`"
          class="flex items-center gap-3 px-4 py-1.5 border-b border-line-faint last:border-b-0 text-sm text-nature-strong opacity-70 cursor-pointer hover:bg-nature-tint-hover"
          @click="openEdit(cont)"
        >
          <i class="pi pi-arrow-down-right text-xs w-4 text-center" />
          <span class="w-24 shrink-0 text-xs">sigue</span>
          <span class="italic">{{ cont.title }}</span>
        </div>
        <!-- dónde se duerme esa noche: sección propia al pie del día -->
        <AgendaBookingSection
          v-if="lodgingRows(day).length"
          tone="lodging"
          title="Alojamiento"
          icon="mdi mdi-bed"
          :tripId="trip.id"
          :rows="lodgingRows(day)"
          position="bottom"
        />
        <p
          v-if="
            !lists[day]?.length &&
            !(continuations.get(day) ?? []).length &&
            !(transportsByDay.get(day) ?? []).length &&
            !(otherBookingsByDay.get(day) ?? []).length &&
            !(lodgingByDay.get(day) ?? []).length
          "
          class="px-4 pb-3 pt-1 text-xs text-ink-disabled"
        >
          Sin actividades
        </p>
      </div>
    </div>

    <div v-else class="bg-surface rounded-card border border-line p-4">
      <ItineraryCalendar :trip="trip" :bookings="bookings.items" @edit="openEdit" />
    </div>

    <ItineraryFormDialog v-model:visible="showForm" :item="editing" :presetDay="presetDay" />
    <CalendarSubscribeDialog v-model:visible="showSubscribe" :trip="trip" />
  </div>
</template>
