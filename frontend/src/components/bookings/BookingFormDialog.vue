<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Textarea from 'primevue/textarea'
import DatePicker from 'primevue/datepicker'
import Select from 'primevue/select'
import AutoComplete from 'primevue/autocomplete'
import DateRangePicker from '../DateRangePicker.vue'
import PayerSelect, { type PayerValue } from '../PayerSelect.vue'
import FormDialog from '../ui/FormDialog.vue'
import FormField from '../ui/FormField.vue'
import type { Booking, BookingType, GeocodeResult, Trip } from '../../api/types'
import {
  BOOKING_TYPE_KEYS,
  CURRENCIES,
  isTransport as isTransportType,
  toSelectOptions,
} from '../../constants'
import { intlLocale } from '../../i18n'
import { useBookingsStore } from '../../stores/bookings'
import { useFormDialog } from '../../composables/useFormDialog'
import { useGeocodeSearch } from '../../composables/useGeocode'
import { toIsoDate } from '../../composables/useMoney'
import { flagEmoji } from '../../countries'

const props = defineProps<{ trip: Trip; booking?: Booking | null }>()
const visible = defineModel<boolean>('visible', { required: true })
const emit = defineEmits<{ saved: [] }>()

const { t } = useI18n()
const store = useBookingsStore()
const { results: geoResults, search: geoSearch } = useGeocodeSearch()

const type = ref<BookingType>('hotel')
const title = ref('')
const provider = ref('')
const confirmationCode = ref('')
const flightNumber = ref('')
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

const typeOptions = computed(() => toSelectOptions(BOOKING_TYPE_KEYS, t))
const numberLocale = computed(() => intlLocale())

const isTransport = computed(() => isTransportType(type.value))
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
    const raw = (await import('../../data/airports.json')).default as [
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
const dateKind = computed(() =>
  type.value === 'hotel' ? 'hotel' : isTransport.value ? 'transport' : 'generic',
)
const dateLabels = computed(() => ({
  start: t(`bookings.form.dates.${dateKind.value}.start`),
  end: t(`bookings.form.dates.${dateKind.value}.end`),
  startTime: t(`bookings.form.dates.${dateKind.value}.startTime`),
  endTime: t(`bookings.form.dates.${dateKind.value}.endTime`),
}))

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

const { saving, save } = useFormDialog({
  visible,
  entity: () => props.booking,
  reset(b) {
    type.value = b?.type ?? 'hotel'
    title.value = b?.title ?? ''
    provider.value = b?.provider ?? ''
    confirmationCode.value = b?.confirmation_code ?? ''
    flightNumber.value = b?.flight_number ?? ''
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
  },
  validate: () => (title.value.trim() ? null : t('bookings.form.titleRequired')),
  submit() {
    const payload = {
      type: type.value,
      title: title.value.trim(),
      provider: provider.value || null,
      confirmation_code: confirmationCode.value || null,
      flight_number: isFlight.value ? flightNumber.value.trim().toUpperCase() || null : null,
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
    return props.booking ? store.update(props.booking.id, payload) : store.create(payload)
  },
  onSaved: () => emit('saved'),
})
</script>

<template>
  <FormDialog
    v-model:visible="visible"
    :header="booking ? $t('bookings.form.editTitle') : $t('bookings.newBooking')"
    :saving="saving"
    :saveLabel="booking ? $t('common.actions.save') : $t('bookings.form.addBooking')"
    @save="save"
  >
    <FormField :label="$t('bookings.form.type')">
      <Select v-model="type" :options="typeOptions" optionLabel="label" optionValue="value" />
    </FormField>

    <!-- lo primero es el lugar, como en Sitios: la selección autorellena el título -->
    <div v-if="isTransport" class="grid grid-cols-2 gap-3">
      <FormField :label="$t('bookings.form.origin')">
        <AutoComplete
          v-if="isFlight"
          v-model="origin"
          :suggestions="airportOptions"
          optionLabel="code"
          :placeholder="$t('bookings.form.originFlightPlaceholder')"
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
        <InputText v-else v-model="origin" :placeholder="$t('bookings.form.originPlaceholder')" />
      </FormField>
      <FormField :label="$t('bookings.form.destination')">
        <AutoComplete
          v-if="isFlight"
          v-model="destination"
          :suggestions="airportOptions"
          optionLabel="code"
          :placeholder="$t('bookings.form.destinationFlightPlaceholder')"
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
        <InputText
          v-else
          v-model="destination"
          :placeholder="$t('bookings.form.destinationPlaceholder')"
        />
      </FormField>
    </div>
    <FormField v-else :label="$t('bookings.form.address')">
      <AutoComplete
        v-model="address"
        :suggestions="geoResults"
        optionLabel="display_name"
        :placeholder="$t('bookings.form.addressPlaceholder')"
        fluid
        autofocus
        @complete="(e) => geoSearch(e.query)"
        @item-select="onAddressSelect"
      />
      <template #hint>
        <p v-if="lat != null && lon != null" class="text-xs text-ink-faint">
          <i class="pi pi-map-marker text-3xs" /> {{ lat.toFixed(5) }}, {{ lon.toFixed(5) }}
        </p>
      </template>
    </FormField>

    <div class="grid grid-cols-2 gap-3">
      <FormField :label="$t('bookings.form.title')" required>
        <InputText v-model="title" :placeholder="$t('bookings.form.titlePlaceholder')" />
      </FormField>
      <FormField :label="$t('bookings.form.provider')">
        <InputText v-model="provider" :placeholder="$t('bookings.form.providerPlaceholder')" />
      </FormField>
    </div>
    <!-- en vuelos: código de reserva (booking) + número de vuelo -->
    <div v-if="isFlight" class="grid grid-cols-2 gap-3">
      <FormField :label="$t('bookings.form.bookingCode')">
        <InputText v-model="confirmationCode" :placeholder="$t('bookings.form.bookingCodePlaceholder')" />
      </FormField>
      <FormField :label="$t('bookings.form.flightNumber')">
        <InputText
          v-model="flightNumber"
          :placeholder="$t('bookings.form.flightNumberPlaceholder')"
          class="font-mono"
        />
      </FormField>
    </div>
    <FormField v-else :label="$t('bookings.form.confirmationCode')">
      <InputText v-model="confirmationCode" />
    </FormField>
    <DateRangePicker
      v-model:start="startDate"
      v-model:end="endDate"
      :startLabel="dateLabels.start"
      :endLabel="dateLabels.end"
      :tripStart="trip.start_date"
      :tripEnd="trip.end_date"
      clearable
    />
    <div class="grid grid-cols-2 gap-3">
      <FormField :label="dateLabels.startTime">
        <DatePicker v-model="startTime" timeOnly hourFormat="24" placeholder="—" />
      </FormField>
      <FormField :label="dateLabels.endTime">
        <DatePicker v-model="endTime" timeOnly hourFormat="24" placeholder="—" />
      </FormField>
    </div>
    <div class="grid grid-cols-2 gap-3">
      <FormField :label="$t('bookings.form.cost')">
        <InputNumber
          v-model="costAmount"
          :minFractionDigits="0"
          :maxFractionDigits="2"
          :locale="numberLocale"
          :min="0"
          :placeholder="$t('bookings.form.costPlaceholder')"
        />
      </FormField>
      <FormField :label="$t('bookings.form.currency')">
        <Select v-model="costCurrency" :options="CURRENCIES" filter />
      </FormField>
      <div class="col-span-2">
        <FormField :label="$t('bookings.form.paidBy')">
          <PayerSelect v-model="paidById" :travelers="trip.travelers" />
          <template #hint>
            <p class="text-xs text-ink-faint">
              {{ $t('bookings.form.payerHint') }}
            </p>
          </template>
        </FormField>
      </div>
    </div>
    <FormField :label="$t('bookings.form.notes')">
      <Textarea v-model="notes" rows="2" autoResize />
    </FormField>
  </FormDialog>
</template>
