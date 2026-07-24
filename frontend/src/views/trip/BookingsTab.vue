<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import BookingFormDialog from '../../components/BookingFormDialog.vue'
import AttachmentList from '../../components/AttachmentList.vue'
import EmptyState from '../../components/EmptyState.vue'
import TabSkeleton from '../../components/TabSkeleton.vue'
import { api } from '../../api/client'
import type { Booking, BookingType, RateRead, Trip } from '../../api/types'
import { BOOKING_TYPE_ICONS, BOOKING_TYPE_LABELS } from '../../constants'
import { useBookingsStore } from '../../stores/bookings'
import { useAttachmentsStore } from '../../stores/attachments'
import { formatDateTime, formatMoney, toIsoDate } from '../../composables/useMoney'

const props = defineProps<{ trip: Trip }>()
const store = useBookingsStore()
const attachments = useAttachmentsStore()
const confirm = useConfirm()
const toast = useToast()

const showForm = ref(false)
const editing = ref<Booking | null>(null)
const creatingExpenseId = ref<number | null>(null)

function loadAll(tripId: number) {
  store.load(tripId)
  attachments.load(tripId)
}

onMounted(() => loadAll(props.trip.id))
watch(() => props.trip.id, loadAll)

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

    <div v-else class="flex flex-col gap-8">
      <section v-for="group in grouped" :key="group.type">
        <h2 class="text-sm font-semibold uppercase tracking-wide text-slate-400 mb-3">
          <i :class="BOOKING_TYPE_ICONS[group.type]" class="mr-1.5" />
          {{ BOOKING_TYPE_LABELS[group.type] }}
        </h2>
        <div class="flex flex-col gap-3">
          <div
            v-for="booking in group.bookings"
            :key="booking.id"
            class="bg-white rounded-xl border border-slate-200 p-4"
          >
            <div class="flex flex-wrap items-start justify-between gap-3">
              <div class="min-w-0">
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
                    v-tooltip.top="'Copiar código'"
                    @click="copyCode(booking.confirmation_code)"
                  />
                </div>
                <div class="flex flex-wrap gap-x-4 gap-y-1 mt-1.5 text-sm text-slate-500">
                  <span v-if="booking.start_dt" class="flex items-center gap-1">
                    <i class="pi pi-calendar text-xs" />
                    {{ formatDateTime(booking.start_dt) }}
                    <template v-if="booking.end_dt"> → {{ formatDateTime(booking.end_dt) }}</template>
                  </span>
                  <span v-if="booking.origin || booking.destination" class="flex items-center gap-1">
                    <i class="pi pi-arrow-right text-xs" />
                    {{ booking.origin ?? '?' }} → {{ booking.destination ?? '?' }}
                  </span>
                  <span v-if="booking.address" class="flex items-center gap-1">
                    <i class="pi pi-map-marker text-xs" /> {{ booking.address }}
                  </span>
                </div>
                <p v-if="booking.notes" class="text-sm text-slate-400 mt-1">{{ booking.notes }}</p>
              </div>
              <div class="flex items-center gap-2 shrink-0">
                <div v-if="booking.cost_amount != null" class="text-right mr-2">
                  <div class="font-semibold text-slate-800">
                    {{ formatMoney(booking.cost_amount, booking.cost_currency ?? trip.base_currency) }}
                  </div>
                  <Button
                    label="Crear gasto"
                    size="small"
                    text
                    icon="pi pi-wallet"
                    :loading="creatingExpenseId === booking.id"
                    @click="createExpense(booking)"
                  />
                </div>
                <Button icon="pi pi-pencil" text size="small" severity="secondary" @click="openEdit(booking)" />
                <Button icon="pi pi-trash" text size="small" severity="danger" @click="removeBooking(booking)" />
              </div>
            </div>
            <div class="mt-3 pt-3 border-t border-slate-100">
              <AttachmentList :bookingId="booking.id" />
            </div>
          </div>
        </div>
      </section>
    </div>

    <BookingFormDialog v-model:visible="showForm" :trip="trip" :booking="editing" />
  </div>
</template>
