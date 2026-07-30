<script lang="ts">
import type { Booking, BookingSegment, BookingSegmentInput } from '../../api/types'
import { toIsoDate } from '../../composables/useMoney'

// Fila local del editor: fechas y horas separadas como en el resto del form
// (una hora 00:00 guardada se trata como "sin hora")
export interface SegmentRow {
  origin: string
  destination: string
  departureDate: Date | null
  departureTime: Date | null
  arrivalDate: Date | null
  arrivalTime: Date | null
  flightNumber: string
}

export function emptySegmentRow(): SegmentRow {
  return {
    origin: '',
    destination: '',
    departureDate: null,
    departureTime: null,
    arrivalDate: null,
    arrivalTime: null,
    flightNumber: '',
  }
}

function timeOf(d: Date): Date | null {
  return d.getHours() || d.getMinutes() ? d : null
}

function rowFromDt(dt: string | null): { date: Date | null; time: Date | null } {
  const parsed = dt ? new Date(dt) : null
  return { date: parsed, time: parsed ? timeOf(parsed) : null }
}

export function rowFromSegment(seg: BookingSegment): SegmentRow {
  const departure = rowFromDt(seg.departure_dt)
  const arrival = rowFromDt(seg.arrival_dt)
  return {
    origin: seg.origin ?? '',
    destination: seg.destination ?? '',
    departureDate: departure.date,
    departureTime: departure.time,
    arrivalDate: arrival.date,
    arrivalTime: arrival.time,
    flightNumber: seg.flight_number ?? '',
  }
}

/** Reservas de antes de los tramos: sus campos planos son el único tramo */
export function rowFromFlatBooking(b: Booking): SegmentRow {
  const departure = rowFromDt(b.start_dt)
  const arrival = rowFromDt(b.end_dt)
  return {
    origin: b.origin ?? '',
    destination: b.destination ?? '',
    departureDate: departure.date,
    departureTime: departure.time,
    arrivalDate: arrival.date,
    arrivalTime: arrival.time,
    flightNumber: b.flight_number ?? '',
  }
}

function toNaiveIso(date: Date, time: Date | null): string {
  const hh = String(time?.getHours() ?? 0).padStart(2, '0')
  const mm = String(time?.getMinutes() ?? 0).padStart(2, '0')
  return `${toIsoDate(date)}T${hh}:${mm}:00`
}

/** Payload del tramo, o null si la fila está en blanco (se descarta) */
export function rowToInput(row: SegmentRow): BookingSegmentInput | null {
  const origin = row.origin.trim()
  const destination = row.destination.trim()
  const flightNumber = row.flightNumber.trim().toUpperCase()
  if (!origin && !destination && !row.departureDate && !row.arrivalDate && !flightNumber) {
    return null
  }
  return {
    origin: origin || null,
    destination: destination || null,
    departure_dt: row.departureDate ? toNaiveIso(row.departureDate, row.departureTime) : null,
    arrival_dt: row.arrivalDate ? toNaiveIso(row.arrivalDate, row.arrivalTime) : null,
    flight_number: flightNumber || null,
  }
}

/** La llegada no puede ser anterior a la salida (mismo criterio que el backend) */
export function rowRangeInvalid(row: SegmentRow): boolean {
  if (!row.departureDate || !row.arrivalDate) return false
  const dep = toNaiveIso(row.departureDate, row.departureTime)
  const arr = toNaiveIso(row.arrivalDate, row.arrivalTime)
  return arr < dep
}
</script>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import InputText from 'primevue/inputtext'
import DatePicker from 'primevue/datepicker'
import AutoComplete from 'primevue/autocomplete'
import Button from 'primevue/button'
import DateRangePicker from '../DateRangePicker.vue'
import FormField from '../ui/FormField.vue'
import type { Trip } from '../../api/types'
import { useAirportSearch } from '../../composables/useAirportSearch'
import { flagEmoji } from '../../countries'

const props = defineProps<{ trip: Trip; isFlight: boolean }>()
const rows = defineModel<SegmentRow[]>({ required: true })

const { t } = useI18n()
const { airportOptions, searchAirports } = useAirportSearch()

function addRow() {
  const last = rows.value[rows.value.length - 1]
  const row = emptySegmentRow()
  if (last) {
    // encadena: el tramo nuevo sale de donde aterrizó (y el día que aterrizó)
    row.origin = last.destination
    row.departureDate = last.arrivalDate ?? last.departureDate
  }
  rows.value = [...rows.value, row]
}

function removeRow(index: number) {
  rows.value = rows.value.filter((_, i) => i !== index)
}

// «Añadir vuelta»: duplica los tramos con ruta en orden inverso y espejado
// (MAD→DOH→NRT ⇒ NRT→DOH→MAD), con fechas y números por rellenar. Se esconde
// cuando el viaje ya vuelve a casa (último destino = primer origen).
const routedRows = computed(() =>
  rows.value.filter((r) => r.origin.trim() && r.destination.trim()),
)
const canAddReturn = computed(() => {
  const routed = routedRows.value
  if (!routed.length) return false
  const first = routed[0].origin.trim().toUpperCase()
  const last = routed[routed.length - 1].destination.trim().toUpperCase()
  return first !== last
})

function addReturn() {
  const mirrored = [...routedRows.value].reverse().map((r) => ({
    ...emptySegmentRow(),
    origin: r.destination,
    destination: r.origin,
  }))
  rows.value = [...rows.value, ...mirrored]
}

// solape entre tramos consecutivos (tal y como están escritos): el aviso es
// suave — no bloquea el guardado, el servidor los reordena por salida
const overlapAt = computed(() =>
  rows.value.map((row, i) => {
    if (!i || !row.departureDate) return false
    const prev = rows.value[i - 1]
    if (!prev.arrivalDate) return false
    const dep = toNaiveIso(row.departureDate, row.departureTime)
    const prevArr = toNaiveIso(prev.arrivalDate, prev.arrivalTime)
    return dep < prevArr
  }),
)
</script>

<template>
  <div class="space-y-3">
    <div
      v-for="(row, index) in rows"
      :key="index"
      class="rounded-lg border border-line p-3 space-y-3"
    >
      <div class="flex items-center justify-between">
        <span class="text-xs font-medium text-ink-secondary">
          {{ t('bookings.form.segments.segmentN', { n: index + 1 }) }}
        </span>
        <Button
          v-if="rows.length > 1"
          icon="pi pi-times"
          text
          rounded
          size="small"
          severity="secondary"
          :aria-label="t('bookings.form.segments.remove')"
          @click="removeRow(index)"
        />
      </div>
      <div class="grid grid-cols-2 gap-3">
        <FormField :label="t('bookings.form.origin')">
          <AutoComplete
            v-if="isFlight"
            v-model="row.origin"
            :suggestions="airportOptions"
            optionLabel="code"
            :placeholder="t('bookings.form.originFlightPlaceholder')"
            dropdown
            fluid
            @complete="searchAirports"
            @item-select="row.origin = $event.value.code"
          >
            <template #option="{ option }">
              <div class="flex items-center gap-2 w-full min-w-0">
                <span class="font-mono font-semibold text-xs w-9 shrink-0">{{ option.code }}</span>
                <span class="truncate text-sm">{{ option.city || option.name }}</span>
                <span class="ml-auto shrink-0 text-sm">{{ flagEmoji(option.country) }}</span>
              </div>
            </template>
          </AutoComplete>
          <InputText v-else v-model="row.origin" :placeholder="t('bookings.form.originPlaceholder')" />
        </FormField>
        <FormField :label="t('bookings.form.destination')">
          <AutoComplete
            v-if="isFlight"
            v-model="row.destination"
            :suggestions="airportOptions"
            optionLabel="code"
            :placeholder="t('bookings.form.destinationFlightPlaceholder')"
            dropdown
            fluid
            @complete="searchAirports"
            @item-select="row.destination = $event.value.code"
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
            v-model="row.destination"
            :placeholder="t('bookings.form.destinationPlaceholder')"
          />
        </FormField>
      </div>
      <DateRangePicker
        v-model:start="row.departureDate"
        v-model:end="row.arrivalDate"
        :startLabel="t('bookings.form.dates.transport.start')"
        :endLabel="t('bookings.form.dates.transport.end')"
        :tripStart="trip.start_date"
        :tripEnd="trip.end_date"
        clearable
      />
      <div class="grid grid-cols-2 gap-3" :class="{ 'sm:grid-cols-3': isFlight }">
        <FormField :label="t('bookings.form.dates.transport.startTime')">
          <DatePicker v-model="row.departureTime" timeOnly hourFormat="24" placeholder="—" />
        </FormField>
        <FormField :label="t('bookings.form.dates.transport.endTime')">
          <DatePicker v-model="row.arrivalTime" timeOnly hourFormat="24" placeholder="—" />
        </FormField>
        <FormField v-if="isFlight" :label="t('bookings.form.flightNumber')" class="col-span-2 sm:col-span-1">
          <InputText
            v-model="row.flightNumber"
            :placeholder="t('bookings.form.flightNumberPlaceholder')"
            class="font-mono"
          />
        </FormField>
      </div>
      <small v-if="rowRangeInvalid(row)" class="text-red-600">
        {{ t('bookings.form.segments.arrivalBeforeDeparture') }}
      </small>
      <small v-else-if="overlapAt[index]" class="text-warn-strong">
        {{ t('bookings.form.segments.overlapWarning') }}
      </small>
    </div>
    <div class="flex items-center gap-2">
      <Button
        icon="pi pi-plus"
        :label="t('bookings.form.segments.add')"
        text
        size="small"
        @click="addRow"
      />
      <Button
        v-if="canAddReturn"
        icon="mdi mdi-swap-horizontal"
        :label="t('bookings.form.segments.addReturn')"
        text
        size="small"
        @click="addReturn"
      />
    </div>
  </div>
</template>
