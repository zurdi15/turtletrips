<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import ClusterBtn from '../../components/ui/ClusterBtn.vue'
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
import AgendaDayJournal from '../../components/itinerary/AgendaDayJournal.vue'
import { API_BASE } from '../../api/client'
import type { ItineraryItem, Trip } from '../../api/types'
import { useItineraryStore } from '../../stores/itinerary'
import { useItineraryJournalStore } from '../../stores/itineraryJournal'
import { usePlacesStore } from '../../stores/places'
import { useBookingsStore } from '../../stores/bookings'
import { useExpensesStore } from '../../stores/expenses'
import { useCrudView } from '../../composables/useCrudView'
import { useTripTabData } from '../../composables/useTripTabData'
import { useWeather } from '../../composables/useWeather'
import { expenseIdByBooking } from '../../utils/expenses'
import { itemCoord, pickDayCoords, weatherIcon, type Coord } from '../../utils/weather'
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
const { t } = useI18n()
const store = useItineraryStore()
const journal = useItineraryJournalStore()
const places = usePlacesStore()
const bookings = useBookingsStore()
const expenses = useExpensesStore()

const view = ref<'agenda' | 'calendar'>('agenda')
const viewOptions = computed(
  () =>
    [
      { value: 'agenda', label: t('itinerary.view.agenda'), icon: 'pi pi-list' },
      { value: 'calendar', label: t('itinerary.view.calendar'), icon: 'pi pi-calendar' },
    ] as const,
)

const showSubscribe = ref(false)
const presetDay = ref<string | null>(null)

const icsUrl = computed(() => `${API_BASE}/trips/${props.trip.id}/calendar.ics`)

useTripTabData(() => props.trip, {
  load(tripId) {
    store.load(tripId)
    journal.load(tripId)
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

// ---- previsión meteo: cabecera = alojamiento de la noche (multi-día
// incluido); cada actividad lleva la de SU sitio (un día puede tocar varias
// zonas si vas en coche) ----

const placeById = computed(() => new Map(places.items.map((p) => [p.id, p])))
const dayCoords = computed(() =>
  pickDayCoords(days.value, lodgingByDay.value, placeById.value),
)
const weatherRequests = computed(() => {
  const requests: { day: string; coord: Coord }[] = []
  for (const [day, coord] of dayCoords.value) requests.push({ day, coord })
  for (const day of days.value) {
    for (const item of store.byDay.get(day) ?? []) {
      const coord = itemCoord(item, placeById.value)
      if (coord) requests.push({ day, coord })
    }
  }
  return requests
})
const { forecastAt } = useWeather(() => weatherRequests.value)

function headerForecast(day: string) {
  return forecastAt(day, dayCoords.value.get(day))
}

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
  return agendaDayLabel(iso, props.trip.start_date, t)
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
    head: transportHead(e, t),
    label: transportLabel(e),
    bookingId: e.b.id,
    placeId: e.b.place_id,
    expenseId: expenseByBooking.value.get(e.b.id) ?? null,
  }))
}

function otherBookingRows(day: string): AgendaRow[] {
  return (otherBookingsByDay.value.get(day) ?? []).map((b) => ({
    key: `o-${b.id}`,
    head: bookingHead(b, t),
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
    head: lodgingHead(b, day, t),
    label: b.title,
    bookingId: b.id,
    placeId: b.place_id,
    expenseId: expenseByBooking.value.get(b.id) ?? null,
  }))
}

// día sin nada de nada: ni actividades, ni continuaciones, ni reservas.
// Solo entonces la lista de actividades vacía reserva alto (zona de drop)
// y se muestra el mensaje "sin actividades"
function dayIsEmpty(day: string): boolean {
  return (
    !lists[day]?.length &&
    !(continuations.value.get(day) ?? []).length &&
    !(transportsByDay.value.get(day) ?? []).length &&
    !(otherBookingsByDay.value.get(day) ?? []).length &&
    !(lodgingByDay.value.get(day) ?? []).length
  )
}

const crud = useCrudView<ItineraryItem>({
  confirm: (item) => ({
    message: t('itinerary.confirm.message', { title: item.title }),
    header: t('itinerary.confirm.header'),
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
      <Button :label="t('itinerary.actions.newActivity')" icon="pi pi-plus" class="w-full sm:w-auto" @click="openNew()" />
      <span class="hidden sm:block flex-1" />
      <ClusterBtn v-model="view" :options="viewOptions" class="flex-1 sm:flex-none" />
      <a :href="icsUrl" download>
        <Button
          :label="t('itinerary.actions.export')"
          icon="pi pi-calendar-plus"
          severity="secondary"
          outlined
          v-tooltip.bottom="t('itinerary.actions.exportTooltip')"
          class="max-sm:[&_.p-button-label]:hidden max-sm:!w-10 max-sm:!h-10 max-sm:!p-0"
        />
      </a>
      <Button
        :label="t('itinerary.actions.subscribe')"
        icon="mdi mdi-calendar-sync"
        severity="secondary"
        outlined
        v-tooltip.bottom="t('itinerary.actions.subscribeTooltip')"
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
      :title="t('itinerary.empty.title')"
      :subtitle="t('itinerary.empty.subtitle')"
    >
      <Button :label="t('itinerary.actions.newActivity')" icon="pi pi-plus" @click="openNew()" />
    </EmptyState>

    <div v-else-if="view === 'agenda'" class="tt-stagger flex flex-col gap-4">
      <div
        v-for="day in days"
        :key="day"
        class="bg-surface rounded-card border border-line overflow-hidden"
      >
        <div class="flex items-center justify-between px-4 py-2.5 bg-surface-muted border-b border-line-subtle">
          <div class="flex items-baseline gap-2 min-w-0">
            <span class="font-semibold text-ink capitalize">{{ dayLabel(day).title }}</span>
            <span class="text-sm text-ink-faint truncate">{{ dayLabel(day).sub }}</span>
          </div>
          <div class="flex items-center gap-2 shrink-0">
            <!-- previsión del alojamiento de la noche (días dentro del horizonte) -->
            <span
              v-if="headerForecast(day)"
              class="flex items-center gap-1.5 text-xs text-ink-muted whitespace-nowrap"
            >
              <i :class="weatherIcon(headerForecast(day)!.weather_code)" class="text-sm" />
              <span class="tabular-nums">
                {{ Math.round(headerForecast(day)!.t_max) }}° / {{ Math.round(headerForecast(day)!.t_min) }}°
              </span>
              <span
                v-if="(headerForecast(day)!.precip_prob ?? 0) >= 30"
                class="text-info"
                v-tooltip.top="t('itinerary.agenda.rainProb', { pct: headerForecast(day)!.precip_prob })"
              >
                <i class="mdi mdi-water text-2xs" />{{ headerForecast(day)!.precip_prob }}%
              </span>
            </span>
            <Button
              icon="pi pi-plus"
              text
              size="small"
              severity="secondary"
              v-tooltip.left="t('itinerary.agenda.addToDay')"
              @click="openNew(day)"
            />
          </div>
        </div>
        <!-- transportes del día: sección propia con cabecera -->
        <AgendaBookingSection
          v-if="transportRows(day).length"
          tone="info"
          :title="t('itinerary.agenda.transport')"
          icon="mdi mdi-plane-train"
          :tripId="trip.id"
          :rows="transportRows(day)"
        />

        <!-- otras reservas del día (actividades, coche…) -->
        <AgendaBookingSection
          v-if="otherBookingRows(day).length"
          tone="warn"
          :title="t('itinerary.agenda.bookings')"
          icon="mdi mdi-ticket-outline"
          :tripId="trip.id"
          :rows="otherBookingRows(day)"
        />

        <!-- sin actividades pero con reservas: la lista colapsa a alto cero
             para no dejar una franja en blanco entre secciones -->
        <draggable
          :list="lists[day]"
          group="itinerary"
          item-key="id"
          handle=".drag-handle"
          :class="{ 'min-h-[2.5rem]': dayIsEmpty(day) }"
          @end="persistOrder"
        >
          <template #item="{ element }">
            <AgendaItemRow
              :item="element"
              :tripId="trip.id"
              :placeName="placeName(element.place_id)"
              :bookingTitle="bookingTitle(element.booking_id)"
              :expenseId="element.booking_id ? (expenseByBooking.get(element.booking_id) ?? null) : null"
              :forecast="forecastAt(day, itemCoord(element, placeById))"
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
          <span class="w-24 shrink-0 text-xs">{{ t('itinerary.agenda.continues') }}</span>
          <span class="italic">{{ cont.title }}</span>
        </div>
        <!-- dónde se duerme esa noche: sección propia al pie del día -->
        <AgendaBookingSection
          v-if="lodgingRows(day).length"
          tone="lodging"
          :title="t('itinerary.agenda.lodging')"
          icon="mdi mdi-bed"
          :tripId="trip.id"
          :rows="lodgingRows(day)"
          position="bottom"
        />
        <p v-if="dayIsEmpty(day)" class="px-4 pb-3 pt-1 text-xs text-ink-disabled">
          {{ t('itinerary.agenda.noActivities') }}
        </p>
        <!-- diario + postal del día (plegable, siempre al pie de la tarjeta) -->
        <AgendaDayJournal :tripId="trip.id" :day="day" />
      </div>
    </div>

    <div v-else class="bg-surface rounded-card border border-line p-4">
      <ItineraryCalendar :trip="trip" :bookings="bookings.items" @edit="openEdit" />
    </div>

    <ItineraryFormDialog v-model:visible="showForm" :item="editing" :presetDay="presetDay" />
    <CalendarSubscribeDialog v-model:visible="showSubscribe" :trip="trip" />
  </div>
</template>
