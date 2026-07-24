<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import BookingFormDialog from '../../components/BookingFormDialog.vue'
import AttachmentList from '../../components/AttachmentList.vue'
import MemberChip from '../../components/MemberChip.vue'
import EmptyState from '../../components/EmptyState.vue'
import TabSkeleton from '../../components/TabSkeleton.vue'
import { api } from '../../api/client'
import type { Booking, BookingType, RateRead, Trip } from '../../api/types'
import { BOOKING_TYPE_ICONS, BOOKING_TYPE_LABELS, TRANSPORT_TYPES } from '../../constants'
import { expenseIdByBooking } from '../../utils/expenses'
import { useBookingsStore } from '../../stores/bookings'
import { useAttachmentsStore } from '../../stores/attachments'
import { useExpensesStore } from '../../stores/expenses'
import { usePlacesStore } from '../../stores/places'
import { formatDateTime, formatMoney, toIsoDate } from '../../composables/useMoney'

const props = defineProps<{ trip: Trip }>()
const store = useBookingsStore()
const attachments = useAttachmentsStore()
const expenses = useExpensesStore()
const places = usePlacesStore()
const confirm = useConfirm()
const toast = useToast()
const route = useRoute()

const showForm = ref(false)
const editing = ref<Booking | null>(null)
const creatingExpenseId = ref<number | null>(null)
const highlightId = ref<number | null>(null)

function loadAll(tripId: number) {
  store.load(tripId)
  attachments.load(tripId)
  expenses.load(tripId)
  places.load(tripId)
}

onMounted(async () => {
  attachments.load(props.trip.id)
  expenses.load(props.trip.id)
  places.load(props.trip.id)
  await store.load(props.trip.id)
  // llegar desde un gasto enlazado (?booking=id) resalta y centra esa reserva
  const fromQuery = Number(route.query.booking)
  if (fromQuery) {
    highlightId.value = fromQuery
    await nextTick()
    document
      .getElementById(`booking-${fromQuery}`)
      ?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    setTimeout(() => (highlightId.value = null), 2600)
  }
})
watch(() => props.trip.id, loadAll)

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

function openNew() {
  editing.value = null
  showForm.value = true
}
function openEdit(booking: Booking) {
  editing.value = booking
  showForm.value = true
}
function removeBooking(booking: Booking) {
  confirm.require({
    message: `¿Eliminar la reserva "${booking.title}"? Sus adjuntos pasarán a nivel de viaje.`,
    header: 'Eliminar reserva',
    icon: 'pi pi-exclamation-triangle',
    rejectProps: { label: 'Cancelar', severity: 'secondary', outlined: true },
    acceptProps: { label: 'Eliminar', severity: 'danger' },
    accept: () => store.remove(booking.id),
  })
}

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
    toast.add({
      severity: 'success',
      summary: 'Gasto creado',
      detail: `${expense.description}: ${formatMoney(expense.amount_base, props.trip.base_currency)}`,
      life: 4000,
    })
    expenses.load(props.trip.id) // refresca el enlace reserva → gasto
  } catch (err) {
    toast.add({ severity: 'error', summary: 'No se pudo crear el gasto', detail: String(err), life: 5000 })
  } finally {
    creatingExpenseId.value = null
  }
}

function copyCode(code: string) {
  navigator.clipboard?.writeText(code)
  toast.add({ severity: 'info', summary: 'Código copiado', life: 2000 })
}
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <Button label="Nueva reserva" icon="pi pi-plus" @click="openNew" />
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
        <h2 class="text-sm font-semibold uppercase tracking-wide text-slate-400 mb-3">
          <i :class="BOOKING_TYPE_ICONS[group.type]" class="mr-1.5" />
          {{ BOOKING_TYPE_LABELS[group.type] }}
        </h2>
        <div class="flex flex-col gap-3">
          <div
            v-for="booking in group.bookings"
            :key="booking.id"
            :id="`booking-${booking.id}`"
            class="bg-white rounded-xl border p-4 transition-shadow duration-500"
            :class="
              highlightId === booking.id
                ? 'border-[var(--p-primary-color)] ring-2 ring-[var(--p-primary-color)]'
                : 'border-slate-200'
            "
          >
            <div class="flex items-start gap-3">
              <!-- izquierda: título y detalles (encoge y trunca, nunca empuja las acciones) -->
              <div class="min-w-0 flex-1">
                <div class="flex items-center gap-2 flex-wrap">
                  <h3 class="font-semibold text-slate-800">{{ booking.title }}</h3>
                  <span v-if="booking.provider" class="text-sm text-slate-400">
                    · {{ booking.provider }}
                  </span>
                  <Tag
                    v-if="booking.confirmation_code"
                    :value="booking.confirmation_code"
                    severity="secondary"
                    class="cursor-pointer font-mono"
                    v-tooltip.top="'Copiar código de reserva'"
                    @click="copyCode(booking.confirmation_code)"
                  />
                  <Tag
                    v-if="booking.flight_number"
                    :value="booking.flight_number"
                    severity="info"
                    class="cursor-pointer font-mono"
                    v-tooltip.top="'Copiar código de vuelo'"
                    @click="copyCode(booking.flight_number)"
                  />
                </div>
                <!-- transporte: origen→destino y fechas en filas separadas (cada
                     una ya lleva su flecha); el resto en línea compacta -->
                <div
                  class="mt-1.5 text-sm text-slate-500"
                  :class="
                    TRANSPORT_TYPES.includes(booking.type)
                      ? 'flex flex-col gap-1 items-start'
                      : 'flex flex-wrap gap-x-4 gap-y-1'
                  "
                >
                  <span v-if="booking.origin || booking.destination" class="flex items-center gap-1.5">
                    <i :class="BOOKING_TYPE_ICONS[booking.type]" class="text-xs" />
                    {{ booking.origin ?? '?' }} → {{ booking.destination ?? '?' }}
                  </span>
                  <span v-if="booking.start_dt" class="flex items-center gap-1.5">
                    <i class="pi pi-calendar text-xs" />
                    {{ formatDateTime(booking.start_dt) }}
                    <template v-if="booking.end_dt"> → {{ formatDateTime(booking.end_dt) }}</template>
                  </span>
                  <span
                    v-if="!booking.place_id && booking.address"
                    class="flex items-center gap-1 min-w-0"
                  >
                    <i class="pi pi-map-marker text-xs shrink-0" />
                    <span class="truncate max-w-[24rem]" v-tooltip.top="booking.address">
                      {{ booking.address }}
                    </span>
                  </span>
                </div>
                <!-- sitio y gasto como iconos, siempre en su propia fila -->
                <div
                  v-if="booking.place_id || expenseByBooking.has(booking.id)"
                  class="mt-1.5 flex items-center gap-2.5 text-sm"
                >
                  <router-link
                    v-if="booking.place_id && placeById.get(booking.place_id)"
                    :to="{ name: 'trip-places', params: { id: trip.id }, query: { place: booking.place_id } }"
                    class="text-emerald-600 no-underline"
                    v-tooltip.top="`Sitio: ${placeById.get(booking.place_id)!.name}`"
                  >
                    <i class="pi pi-map-marker text-xs" />
                  </router-link>
                  <router-link
                    v-if="expenseByBooking.has(booking.id)"
                    :to="{
                      name: 'trip-expenses',
                      params: { id: trip.id },
                      query: { expense: expenseByBooking.get(booking.id) },
                    }"
                    class="text-amber-600 no-underline"
                    v-tooltip.top="'Ver gasto'"
                  >
                    <i class="pi pi-wallet text-xs" />
                  </router-link>
                </div>
                <p v-if="booking.notes" class="text-sm text-slate-400 mt-1">{{ booking.notes }}</p>
              </div>

              <!-- derecha: importe + acciones en una línea, y el gasto debajo -->
              <div class="flex flex-col items-end shrink-0">
                <div class="flex items-center gap-1">
                  <span
                    v-if="booking.cost_amount != null"
                    class="font-semibold text-slate-800 mr-1.5 whitespace-nowrap"
                  >
                    {{ formatMoney(booking.cost_amount, booking.cost_currency ?? trip.base_currency) }}
                  </span>
                  <Button icon="pi pi-pencil" text size="small" severity="secondary" @click="openEdit(booking)" />
                  <Button icon="pi pi-trash" text size="small" severity="danger" @click="removeBooking(booking)" />
                </div>
                <span
                  v-if="booking.paid_by_common"
                  class="inline-flex items-center gap-1.5 px-2 py-0.5 mt-0.5 rounded-full text-xs font-medium bg-amber-50 text-amber-700"
                  v-tooltip.left="'Pagado del fondo común'"
                >
                  <i class="pi pi-wallet text-[10px]" />
                  Común
                </span>
                <MemberChip
                  v-else-if="booking.paid_by_id != null && memberById.get(booking.paid_by_id)"
                  :member="memberById.get(booking.paid_by_id)!"
                  class="mt-0.5"
                />
                <!-- normalmente el gasto nace solo con la reserva; este botón es
                     la vía de regeneración (gasto borrado o tasa no disponible) -->
                <Button
                  v-if="booking.cost_amount != null && !expenseByBooking.has(booking.id)"
                  label="Crear gasto"
                  size="small"
                  text
                  icon="pi pi-wallet"
                  :loading="creatingExpenseId === booking.id"
                  @click="createExpense(booking)"
                />
              </div>
            </div>
            <div class="mt-3 pt-3 border-t border-slate-100">
              <AttachmentList :bookingId="booking.id" />
            </div>
          </div>
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
