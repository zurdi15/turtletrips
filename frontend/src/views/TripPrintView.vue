<script setup lang="ts">
import { computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import TabSkeleton from '../components/TabSkeleton.vue'
import PrintToolbar from '../components/print/PrintToolbar.vue'
import TripPrintDocument from '../components/print/TripPrintDocument.vue'
import { useTripsStore } from '../stores/trips'
import { usePlacesStore } from '../stores/places'
import { useItineraryStore } from '../stores/itinerary'
import { useBookingsStore } from '../stores/bookings'
import { useExpensesStore } from '../stores/expenses'
import { usePrintPage } from '../composables/usePrintPage'
import { usePrintTripData } from '../composables/usePrintTripData'
import { printDocumentTitle } from '../utils/print'

// Versión imprimible del viaje CON sesión: aquí sí caben los gastos.
const props = defineProps<{ id: string }>()

const { t } = useI18n()
const tripId = computed(() => Number(props.id))

const trips = useTripsStore()
const places = usePlacesStore()
const itinerary = useItineraryStore()
const bookings = useBookingsStore()
const expenses = useExpensesStore()

const { options, print, setTitle } = usePrintPage(true)

watch(
  tripId,
  (id) => {
    if (!Number.isFinite(id)) return
    trips.loadTrip(id)
    places.load(id)
    itinerary.load(id)
    bookings.load(id)
    expenses.load(id)
  },
  { immediate: true },
)

// `loadTrip` deja el viaje en `current`: la lista solo se llena en el listado y
// aquí se entra por URL directa (o desde Ajustes), sin pasar por él
const trip = computed(() => (trips.current?.id === tripId.value ? trips.current : null))

const doc = usePrintTripData({
  trip: () =>
    trip.value && {
      name: trip.value.name,
      countries: trip.value.countries,
      start_date: trip.value.start_date,
      end_date: trip.value.end_date,
      notes: trip.value.notes,
      cover_url: trip.value.cover_url,
      travelers: trip.value.travelers.map((who) => ({ name: who.name, color: who.color })),
    },
  places: () => places.items,
  items: () => itinerary.items,
  bookings: () => bookings.items,
  hasExpenses: () => (expenses.summary?.expense_count ?? 0) > 0,
  options,
  t,
})

watch(
  () => trip.value?.name,
  (name) => name && setTitle(printDocumentTitle(name, trip.value?.start_date ?? null)),
  { immediate: true },
)
</script>

<template>
  <div class="min-h-screen -mt-6 bg-page">
    <PrintToolbar
      v-model:options="options"
      :backTo="`/trips/${id}/settings`"
      allowExpenses
      @print="print"
    />
    <div class="max-w-4xl mx-auto py-6">
      <TabSkeleton v-if="!trip" variant="cards" :rows="3" />
      <TripPrintDocument
        v-else-if="doc.trip.value"
        :trip="doc.trip.value"
        :days="doc.days.value"
        :places="places.items"
        :bookings="bookings.items"
        :route="doc.route.value"
        :summary="options.expenses ? expenses.summary : null"
        :options="options"
        :sections="doc.sections.value"
      />
    </div>
  </div>
</template>
