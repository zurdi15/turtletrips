<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import { useRoute } from 'vue-router'
import Button from 'primevue/button'
import BookingFormDialog from '../../components/bookings/BookingFormDialog.vue'
import BookingCard from '../../components/bookings/BookingCard.vue'
import EmptyState from '../../components/EmptyState.vue'
import TabSkeleton from '../../components/TabSkeleton.vue'
import { api } from '../../api/client'
import type { Booking, BookingType, RateRead, Trip } from '../../api/types'
import { BOOKING_TYPE_ICONS, BOOKING_TYPE_LABELS } from '../../constants'
import { expenseIdByBooking } from '../../utils/expenses'
import { useBookingsStore } from '../../stores/bookings'
import { useAttachmentsStore } from '../../stores/attachments'
import { useExpensesStore } from '../../stores/expenses'
import { usePlacesStore } from '../../stores/places'
import { formatMoney, toIsoDate } from '../../composables/useMoney'
import { useNotify } from '../../composables/useNotify'
import { useCrudView } from '../../composables/useCrudView'
import { useTripTabData } from '../../composables/useTripTabData'

const props = defineProps<{ trip: Trip }>()
const store = useBookingsStore()
const attachments = useAttachmentsStore()
const expenses = useExpensesStore()
const places = usePlacesStore()
const notify = useNotify()
const route = useRoute()

const creatingExpenseId = ref<number | null>(null)
const highlightId = ref<number | null>(null)

useTripTabData(() => props.trip, {
  load(tripId) {
    attachments.load(tripId)
    expenses.load(tripId)
    places.load(tripId)
    return store.load(tripId)
  },
  // llegar desde un gasto enlazado (?booking=id) resalta y centra esa reserva
  async afterFirstLoad() {
    const fromQuery = Number(route.query.booking)
    if (!fromQuery) return
    highlightId.value = fromQuery
    await nextTick()
    document
      .getElementById(`booking-${fromQuery}`)
      ?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    setTimeout(() => (highlightId.value = null), 2600)
  },
})

// gasto ya generado desde cada reserva: bloquea el botón "Crear gasto"
const expenseByBooking = computed(() => expenseIdByBooking(expenses.items))

const placeById = computed(() => new Map(places.items.map((p) => [p.id, p])))
const memberById = computed(() => new Map(props.trip.travelers.map((t) => [t.id, t])))

const TYPE_ORDER: BookingType[] = [
  'flight', 'train', 'bus', 'ferry', 'car_rental', 'hotel', 'activity', 'other',
]

const grouped = computed(() =>
  TYPE_ORDER.map((type) => ({
    type,
    bookings: store.items.filter((b) => b.type === type),
  })).filter((g) => g.bookings.length),
)

const {
  showForm,
  editing,
  openNew,
  openEdit,
  removeItem: removeBooking,
} = useCrudView<Booking>({
  confirm: (booking) => ({
    message: `¿Eliminar la reserva "${booking.title}"? Sus adjuntos pasarán a nivel de viaje.`,
    header: 'Eliminar reserva',
  }),
  remove: (booking) => store.remove(booking.id),
})

async function createExpense(booking: Booking) {
  creatingExpenseId.value = booking.id
  try {
    // obtener la tasa aquí permite un mensaje claro si no está disponible
    let rate: number | undefined
    if (booking.cost_currency && booking.cost_currency !== props.trip.base_currency) {
      const day = booking.start_dt ? booking.start_dt.slice(0, 10) : toIsoDate(new Date())
      try {
        const r = await api.get<RateRead>(
          `/rates?from=${booking.cost_currency}&to=${props.trip.base_currency}&date=${day}`,
        )
        rate = r.rate
      } catch {
        rate = undefined // el backend lo intentará también
      }
    }
    const expense = await store.createExpense(booking.id, rate)
    notify.success(
      'Gasto creado',
      `${expense.description}: ${formatMoney(expense.amount_base, props.trip.base_currency)}`,
    )
    expenses.load(props.trip.id) // refresca el enlace reserva → gasto
  } catch (err) {
    notify.error('No se pudo crear el gasto', err)
  } finally {
    creatingExpenseId.value = null
  }
}

function copyCode(code: string) {
  navigator.clipboard?.writeText(code)
  notify.info('Código copiado')
}
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <Button label="Nueva reserva" icon="pi pi-plus" class="w-full sm:w-auto" @click="openNew" />
    </div>

    <TabSkeleton v-if="store.loading && !store.items.length" variant="cards" :rows="3" />

    <EmptyState
      v-else-if="!store.items.length"
      icon="pi pi-ticket"
      title="Sin reservas"
      subtitle="Guarda aquí hoteles, vuelos y actividades con sus PDFs"
    />

    <div v-else class="tt-stagger flex flex-col gap-8">
      <section v-for="group in grouped" :key="group.type">
        <h2 class="text-sm font-semibold uppercase tracking-wide text-ink-faint mb-3">
          <i :class="BOOKING_TYPE_ICONS[group.type]" class="mr-1.5" />
          {{ BOOKING_TYPE_LABELS[group.type] }}
        </h2>
        <div class="flex flex-col gap-3">
          <BookingCard
            v-for="booking in group.bookings"
            :key="booking.id"
            :booking="booking"
            :trip="trip"
            :placeName="booking.place_id ? (placeById.get(booking.place_id)?.name ?? null) : null"
            :expenseId="expenseByBooking.get(booking.id) ?? null"
            :payer="booking.paid_by_id != null ? (memberById.get(booking.paid_by_id) ?? null) : null"
            :highlighted="highlightId === booking.id"
            :creatingExpense="creatingExpenseId === booking.id"
            @edit="openEdit(booking)"
            @remove="removeBooking(booking)"
            @create-expense="createExpense(booking)"
            @copy-code="copyCode"
          />
        </div>
      </section>
    </div>

    <!-- al guardar, el backend puede crear/enlazar sitio y sincronizar el gasto -->
    <BookingFormDialog
      v-model:visible="showForm"
      :trip="trip"
      :booking="editing"
      @saved="places.load(trip.id); expenses.load(trip.id)"
    />
  </div>
</template>
