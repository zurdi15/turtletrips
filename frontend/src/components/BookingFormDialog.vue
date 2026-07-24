<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Textarea from 'primevue/textarea'
import DatePicker from 'primevue/datepicker'
import Select from 'primevue/select'
import Button from 'primevue/button'
import DateRangePicker from './DateRangePicker.vue'
import { useToast } from 'primevue/usetoast'
import type { Booking, BookingType, Trip } from '../api/types'
import { BOOKING_TYPE_LABELS, CURRENCIES, toSelectOptions } from '../constants'
import { useBookingsStore } from '../stores/bookings'
import { toIsoDate } from '../composables/useMoney'

const props = defineProps<{ trip: Trip; booking?: Booking | null }>()
const visible = defineModel<boolean>('visible', { required: true })
const emit = defineEmits<{ saved: [] }>()

const toast = useToast()
const store = useBookingsStore()

const type = ref<BookingType>('hotel')
const title = ref('')
const provider = ref('')
const confirmationCode = ref('')
const startDate = ref<Date | null>(null)
const endDate = ref<Date | null>(null)
const startTime = ref<Date | null>(null)
const endTime = ref<Date | null>(null)
const origin = ref('')
const destination = ref('')
const address = ref('')
const costAmount = ref<number | null>(null)
const costCurrency = ref<string | null>(null)
const notes = ref('')
const saving = ref(false)

const typeOptions = toSelectOptions(BOOKING_TYPE_LABELS)

const isTransport = computed(() => ['flight', 'train', 'bus', 'ferry'].includes(type.value))
const dateLabels = computed(() =>
  type.value === 'hotel'
    ? { start: 'Check-in', end: 'Check-out' }
    : isTransport.value
      ? { start: 'Salida', end: 'Llegada' }
      : { start: 'Inicio', end: 'Fin' },
)

function toNaiveIso(date: Date, time: Date | null): string {
  const hh = String(time?.getHours() ?? 0).padStart(2, '0')
  const mm = String(time?.getMinutes() ?? 0).padStart(2, '0')
  return `${toIsoDate(date)}T${hh}:${mm}:00`
}

// una hora 00:00 guardada se trata como "sin hora"
function timeOf(d: Date): Date | null {
  return d.getHours() || d.getMinutes() ? d : null
}

watch(visible, (open) => {
  if (!open) return
  const b = props.booking
  type.value = b?.type ?? 'hotel'
  title.value = b?.title ?? ''
  provider.value = b?.provider ?? ''
  confirmationCode.value = b?.confirmation_code ?? ''
  const start = b?.start_dt ? new Date(b.start_dt) : null
  const end = b?.end_dt ? new Date(b.end_dt) : null
  startDate.value = start
  endDate.value = end
  startTime.value = start ? timeOf(start) : null
  endTime.value = end ? timeOf(end) : null
  origin.value = b?.origin ?? ''
  destination.value = b?.destination ?? ''
  address.value = b?.address ?? ''
  costAmount.value = b?.cost_amount ?? null
  costCurrency.value = b?.cost_currency ?? props.trip.base_currency
  notes.value = b?.notes ?? ''
})

async function save() {
  if (!title.value.trim()) {
    toast.add({ severity: 'warn', summary: 'El título es obligatorio', life: 3000 })
    return
  }
  saving.value = true
  try {
    const payload = {
      type: type.value,
      title: title.value.trim(),
      provider: provider.value || null,
      confirmation_code: confirmationCode.value || null,
      start_dt: startDate.value ? toNaiveIso(startDate.value, startTime.value) : null,
      end_dt: endDate.value ? toNaiveIso(endDate.value, endTime.value) : null,
      origin: isTransport.value ? origin.value || null : null,
      destination: isTransport.value ? destination.value || null : null,
      address: !isTransport.value ? address.value || null : null,
      cost_amount: costAmount.value,
      cost_currency: costAmount.value != null ? costCurrency.value : null,
      notes: notes.value || null,
    }
    if (props.booking) await store.update(props.booking.id, payload)
    else await store.create(payload)
    visible.value = false
    emit('saved')
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error al guardar', detail: String(err), life: 5000 })
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <Dialog
    v-model:visible="visible"
    modal
    :header="booking ? 'Editar reserva' : 'Nueva reserva'"
    class="w-full max-w-lg mx-4"
  >
    <div class="flex flex-col gap-4">
      <div class="grid grid-cols-2 gap-3">
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">Tipo</label>
          <Select v-model="type" :options="typeOptions" optionLabel="label" optionValue="value" />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">Título *</label>
          <InputText v-model="title" placeholder="Hotel Gracery Shinjuku" />
        </div>
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">Proveedor</label>
          <InputText v-model="provider" placeholder="Booking.com, Iberia…" />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">Código de confirmación</label>
          <InputText v-model="confirmationCode" />
        </div>
      </div>
      <DateRangePicker
        v-model:start="startDate"
        v-model:end="endDate"
        :startLabel="dateLabels.start"
        :endLabel="dateLabels.end"
        clearable
      />
      <div class="grid grid-cols-2 gap-3">
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">Hora {{ dateLabels.start.toLowerCase() }}</label>
          <DatePicker v-model="startTime" timeOnly hourFormat="24" placeholder="—" />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">Hora {{ dateLabels.end.toLowerCase() }}</label>
          <DatePicker v-model="endTime" timeOnly hourFormat="24" placeholder="—" />
        </div>
      </div>
      <div v-if="isTransport" class="grid grid-cols-2 gap-3">
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">Origen</label>
          <InputText v-model="origin" placeholder="MAD" />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">Destino</label>
          <InputText v-model="destination" placeholder="NRT" />
        </div>
      </div>
      <div v-else class="flex flex-col gap-1">
        <label class="text-sm font-medium">Dirección</label>
        <InputText v-model="address" />
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">Coste</label>
          <InputNumber
            v-model="costAmount"
            :minFractionDigits="0"
            :maxFractionDigits="2"
            locale="es-ES"
            :min="0"
            placeholder="Opcional"
          />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">Moneda</label>
          <Select v-model="costCurrency" :options="CURRENCIES" filter />
        </div>
      </div>
      <div class="flex flex-col gap-1">
        <label class="text-sm font-medium">Notas</label>
        <Textarea v-model="notes" rows="2" autoResize />
      </div>
    </div>
    <template #footer>
      <Button label="Cancelar" severity="secondary" text @click="visible = false" />
      <Button :label="booking ? 'Guardar' : 'Añadir reserva'" :loading="saving" @click="save" />
    </template>
  </Dialog>
</template>
