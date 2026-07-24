<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Textarea from 'primevue/textarea'
import DatePicker from 'primevue/datepicker'
import Select from 'primevue/select'
import Button from 'primevue/button'
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
const startDt = ref<Date | null>(null)
const endDt = ref<Date | null>(null)
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

function toNaiveIso(d: Date): string {
  const hh = String(d.getHours()).padStart(2, '0')
  const mm = String(d.getMinutes()).padStart(2, '0')
  return `${toIsoDate(d)}T${hh}:${mm}:00`
}

watch(visible, (open) => {
  if (!open) return
  const b = props.booking
  type.value = b?.type ?? 'hotel'
  title.value = b?.title ?? ''
  provider.value = b?.provider ?? ''
  confirmationCode.value = b?.confirmation_code ?? ''
  startDt.value = b?.start_dt ? new Date(b.start_dt) : null
  endDt.value = b?.end_dt ? new Date(b.end_dt) : null
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
      start_dt: startDt.value ? toNaiveIso(startDt.value) : null,
      end_dt: endDt.value ? toNaiveIso(endDt.value) : null,
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
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">{{ dateLabels.start }}</label>
          <DatePicker v-model="startDt" showTime hourFormat="24" showIcon dateFormat="dd/mm/yy" />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">{{ dateLabels.end }}</label>
          <DatePicker v-model="endDt" showTime hourFormat="24" showIcon dateFormat="dd/mm/yy" />
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
