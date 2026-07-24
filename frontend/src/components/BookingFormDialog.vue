<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Textarea from 'primevue/textarea'
import DatePicker from 'primevue/datepicker'
import Select from 'primevue/select'
import Button from 'primevue/button'
import AutoComplete from 'primevue/autocomplete'
import DateRangePicker from './DateRangePicker.vue'
import PayerSelect, { type PayerValue } from './PayerSelect.vue'
import { useToast } from 'primevue/usetoast'
import type { Booking, BookingType, GeocodeResult, Trip } from '../api/types'
import { BOOKING_TYPE_LABELS, CURRENCIES, toSelectOptions } from '../constants'
import { useBookingsStore } from '../stores/bookings'
import { useGeocodeSearch } from '../composables/useGeocode'
import { toIsoDate } from '../composables/useMoney'
import { flagEmoji } from '../countries'

const props = defineProps<{ trip: Trip; booking?: Booking | null }>()
const visible = defineModel<boolean>('visible', { required: true })
const emit = defineEmits<{ saved: [] }>()

const toast = useToast()
const store = useBookingsStore()
const { results: geoResults, search: geoSearch } = useGeocodeSearch()

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
const address = ref<string | GeocodeResult>('')
const lat = ref<number | null>(null)
const lon = ref<number | null>(null)
// dirección que produjo las coordenadas; si el texto cambia, las coordenadas caducan
const locatedAddress = ref<string | null>(null)
const costAmount = ref<number | null>(null)
const costCurrency = ref<string | null>(null)
const paidById = ref<PayerValue>(null)
const notes = ref('')
const saving = ref(false)

function addressText(): string {
  return typeof address.value === 'string' ? address.value : address.value.display_name
}

function onAddressSelect(event: { value: GeocodeResult }) {
  const r = event.value
  address.value = r.display_name
  lat.value = r.lat
  lon.value = r.lon
  locatedAddress.value = r.display_name
  // el título se autorellena con el nombre del lugar; se puede editar después
  title.value = r.display_name.split(',')[0].trim()
}

watch(address, () => {
  if (locatedAddress.value != null && addressText() !== locatedAddress.value) {
    lat.value = null
    lon.value = null
    locatedAddress.value = null
  }
})

const typeOptions = toSelectOptions(BOOKING_TYPE_LABELS)

const isTransport = computed(() => ['flight', 'train', 'bus', 'ferry'].includes(type.value))
const isFlight = computed(() => type.value === 'flight')

// vuelos: buscador de aeropuertos (IATA) — dataset lazy, solo se carga al usarlo
interface Airport {
  code: string
  name: string
  city: string
  country: string
}
let airportsCache: Airport[] | null = null
const airportOptions = ref<Airport[]>([])

async function loadAirports(): Promise<Airport[]> {
  if (!airportsCache) {
    const raw = (await import('../data/airports.json')).default as [
      string, string, string, string,
    ][]
    airportsCache = raw.map(([code, name, city, country]) => ({ code, name, city, country }))
  }
  return airportsCache
}

async function searchAirports(event: { query: string }) {
  const all = await loadAirports()
  const q = event.query.trim().toLowerCase()
  if (!q) {
    airportOptions.value = all.slice(0, 20)
    return
  }
  const code = q.toUpperCase()
  const byCode = all.filter((a) => a.code.startsWith(code))
  const byText = all.filter(
    (a) =>
      !a.code.startsWith(code) &&
      (a.city.toLowerCase().includes(q) || a.name.toLowerCase().includes(q)),
  )
  airportOptions.value = [...byCode, ...byText].slice(0, 20)
}
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

function timeAt(hours: number, minutes = 0): Date {
  const d = new Date()
  d.setHours(hours, minutes, 0, 0)
  return d
}

function isTime(d: Date | null, hours: number, minutes = 0): boolean {
  return d != null && d.getHours() === hours && d.getMinutes() === minutes
}

// hoteles: check-in 15:00 y check-out 11:00 por defecto (solo al crear;
// al editar se respetan las horas guardadas). Cambiar de tipo retira las
// horas por defecto si no se tocaron.
watch(type, (t, prev) => {
  if (props.booking) return
  if (t === 'hotel') {
    startTime.value ??= timeAt(15)
    endTime.value ??= timeAt(11)
  } else if (prev === 'hotel') {
    if (isTime(startTime.value, 15)) startTime.value = null
    if (isTime(endTime.value, 11)) endTime.value = null
  }
})

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
  if (!b) {
    // reserva nueva: arranca como hotel, con sus horas por defecto
    startTime.value = timeAt(15)
    endTime.value = timeAt(11)
  }
  origin.value = b?.origin ?? ''
  destination.value = b?.destination ?? ''
  address.value = b?.address ?? ''
  lat.value = b?.lat ?? null
  lon.value = b?.lon ?? null
  locatedAddress.value = b?.lat != null ? (b?.address ?? null) : null
  costAmount.value = b?.cost_amount ?? null
  costCurrency.value = b?.cost_currency ?? props.trip.base_currency
  paidById.value = b?.paid_by_common ? 'common' : (b?.paid_by_id ?? null)
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
      address: !isTransport.value ? addressText() || null : null,
      lat: !isTransport.value ? lat.value : null,
      lon: !isTransport.value ? lon.value : null,
      cost_amount: costAmount.value,
      cost_currency: costAmount.value != null ? costCurrency.value : null,
      paid_by_id: paidById.value === 'common' ? null : paidById.value,
      paid_by_common: paidById.value === 'common',
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
      <div class="flex flex-col gap-1">
        <label class="text-sm font-medium">Tipo</label>
        <Select v-model="type" :options="typeOptions" optionLabel="label" optionValue="value" />
      </div>

      <!-- lo primero es el lugar, como en Sitios: la selección autorellena el título -->
      <div v-if="isTransport" class="grid grid-cols-2 gap-3">
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">Origen</label>
          <AutoComplete
            v-if="isFlight"
            v-model="origin"
            :suggestions="airportOptions"
            optionLabel="code"
            placeholder="MAD, Madrid…"
            dropdown
            fluid
            @complete="searchAirports"
            @item-select="origin = $event.value.code"
          >
            <template #option="{ option }">
              <div class="flex items-center gap-2 w-full min-w-0">
                <span class="font-mono font-semibold text-xs w-9 shrink-0">{{ option.code }}</span>
                <span class="truncate text-sm">{{ option.city || option.name }}</span>
                <span class="ml-auto shrink-0 text-sm">{{ flagEmoji(option.country) }}</span>
              </div>
            </template>
          </AutoComplete>
          <InputText v-else v-model="origin" placeholder="Madrid" />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">Destino</label>
          <AutoComplete
            v-if="isFlight"
            v-model="destination"
            :suggestions="airportOptions"
            optionLabel="code"
            placeholder="NRT, Tokio…"
            dropdown
            fluid
            @complete="searchAirports"
            @item-select="destination = $event.value.code"
          >
            <template #option="{ option }">
              <div class="flex items-center gap-2 w-full min-w-0">
                <span class="font-mono font-semibold text-xs w-9 shrink-0">{{ option.code }}</span>
                <span class="truncate text-sm">{{ option.city || option.name }}</span>
                <span class="ml-auto shrink-0 text-sm">{{ flagEmoji(option.country) }}</span>
              </div>
            </template>
          </AutoComplete>
          <InputText v-else v-model="destination" placeholder="Tokio" />
        </div>
      </div>
      <div v-else class="flex flex-col gap-1">
        <label class="text-sm font-medium">Dirección</label>
        <AutoComplete
          v-model="address"
          :suggestions="geoResults"
          optionLabel="display_name"
          placeholder="Busca un lugar o dirección…"
          fluid
          autofocus
          @complete="(e) => geoSearch(e.query)"
          @item-select="onAddressSelect"
        />
        <p v-if="lat != null && lon != null" class="text-xs text-slate-400">
          <i class="pi pi-map-marker text-[10px]" /> {{ lat.toFixed(5) }}, {{ lon.toFixed(5) }}
        </p>
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">Título *</label>
          <InputText v-model="title" placeholder="Hotel Gracery Shinjuku" />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">Proveedor</label>
          <InputText v-model="provider" placeholder="Booking.com, Iberia…" />
        </div>
      </div>
      <div class="flex flex-col gap-1">
        <label class="text-sm font-medium">Código de confirmación</label>
        <InputText v-model="confirmationCode" />
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
        <div class="flex flex-col gap-1 col-span-2">
          <label class="text-sm font-medium">Pagado por</label>
          <PayerSelect v-model="paidById" :travelers="trip.travelers" />
          <p class="text-xs text-slate-400">
            Con coste, la reserva crea su gasto automáticamente y hereda este pagador
          </p>
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
