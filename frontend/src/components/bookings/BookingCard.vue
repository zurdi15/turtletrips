<script setup lang="ts">
import { computed } from 'vue'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import AttachmentList from '../AttachmentList.vue'
import MemberChip from '../MemberChip.vue'
import Pill from '../ui/Pill.vue'
import RowActions from '../ui/RowActions.vue'
import EntityLink from '../trip/EntityLink.vue'
import type { Booking, Traveler, Trip } from '../../api/types'
import { BOOKING_TYPE_ICONS, isTransport } from '../../constants'
import { formatDateTime, formatMoney } from '../../composables/useMoney'
import { groupJourneys, layoverInfo, segmentLabel } from '../../utils/segments'

const props = defineProps<{
  booking: Booking
  trip: Trip
  /** nombre del sitio enlazado (para el tooltip del chip) */
  placeName: string | null
  /** gasto generado desde la reserva; null si no existe (habilita "Crear gasto") */
  expenseId: number | null
  payer: Traveler | null
  highlighted: boolean
  creatingExpense: boolean
}>()
defineEmits<{ edit: []; remove: []; 'create-expense': []; 'copy-code': [code: string] }>()

// trayectos derivados de los tramos (ida vs vuelta por hueco); con tramos la
// fila agregada origen→destino/fechas se calla y hablan ellos
const journeys = computed(() => groupJourneys(props.booking.segments ?? []))
const hasSegments = computed(() => (props.booking.segments ?? []).length > 0)

</script>

<template>
  <div
    :id="`booking-${booking.id}`"
    class="bg-surface rounded-card border p-4 transition-shadow duration-500"
    :class="
      highlighted
        ? 'border-primary ring-2 ring-primary'
        : 'border-line'
    "
  >
    <!-- grid de 2 columnas: en móvil los detalles y el pagador ocupan todo el
         ancho (filas propias) para que no los estruje la columna de acciones -->
    <div class="grid grid-cols-[minmax(0,1fr)_auto] gap-x-3">
      <!-- título -->
      <div class="row-start-1 col-start-1 min-w-0 self-start flex items-center gap-2 flex-wrap">
        <h3 class="font-semibold text-ink-heading">{{ booking.title }}</h3>
        <span v-if="booking.provider" class="text-sm text-ink-faint">
          {{ booking.provider }}
        </span>
        <Tag
          v-if="booking.confirmation_code"
          :value="booking.confirmation_code"
          severity="secondary"
          class="cursor-pointer font-mono"
          v-tooltip.top="$t('bookings.card.copyBookingCode')"
          @click="$emit('copy-code', booking.confirmation_code!)"
        />
        <Tag
          v-if="booking.flight_number"
          :value="booking.flight_number"
          severity="info"
          class="cursor-pointer font-mono"
          v-tooltip.top="$t('bookings.card.copyFlightCode')"
          @click="$emit('copy-code', booking.flight_number!)"
        />
      </div>

      <!-- importe + acciones: en la fila del título, sin estirarse con ella
           (self-start) y subidos el padding del botón (-mt-1) para que queden
           centrados en la PRIMERA línea del nombre aunque el título salte -->
      <div class="row-start-1 col-start-2 flex items-center gap-1 self-start -mt-1 shrink-0">
        <span
          v-if="booking.cost_amount != null"
          class="font-semibold text-ink-heading mr-1.5 whitespace-nowrap"
        >
          {{ formatMoney(booking.cost_amount, booking.cost_currency ?? trip.base_currency) }}
        </span>
        <RowActions always @edit="$emit('edit')" @remove="$emit('remove')" />
      </div>

      <!-- detalles: a todo el ancho en móvil, bajo el título en escritorio -->
      <div class="row-start-2 col-span-2 sm:col-start-1 sm:col-span-1 min-w-0">
        <!-- transporte: origen→destino y fechas en filas separadas (cada
             una ya lleva su flecha); el resto en línea compacta -->
        <div
          class="mt-1.5 text-sm text-ink-muted"
          :class="
            isTransport(booking.type)
              ? 'flex flex-col gap-1 items-start'
              : 'flex flex-wrap gap-x-4 gap-y-1'
          "
        >
          <!-- con tramos hablan los trayectos (con sus escalas); sin ellos,
               la ruta y fechas planas de siempre -->
          <template v-if="hasSegments">
            <div
              v-for="(journey, j) in journeys"
              :key="j"
              class="flex flex-col gap-1 items-start"
              :class="{ 'mt-1': j > 0 }"
            >
              <span v-if="journeys.length > 1" class="text-2xs font-medium uppercase tracking-wide text-ink-faint">
                {{ $t('bookings.card.journeyN', { n: j + 1 }) }}
              </span>
              <template v-for="(seg, i) in journey" :key="seg.id">
                <span class="flex items-center gap-1.5 flex-wrap">
                  <i :class="BOOKING_TYPE_ICONS[booking.type]" class="text-xs" />
                  {{ segmentLabel(seg) ?? booking.title }}
                  <span v-if="seg.departure_dt" class="text-ink-faint">
                    {{ formatDateTime(seg.departure_dt) }}
                    <template v-if="seg.arrival_dt"> → {{ formatDateTime(seg.arrival_dt) }}</template>
                  </span>
                  <Tag
                    v-if="seg.flight_number"
                    :value="seg.flight_number"
                    severity="info"
                    class="cursor-pointer font-mono"
                    v-tooltip.top="$t('bookings.card.copyFlightCode')"
                    @click="$emit('copy-code', seg.flight_number!)"
                  />
                </span>
                <span
                  v-if="layoverInfo(journey, i)"
                  class="flex items-center gap-1.5 text-xs pl-4"
                  :class="layoverInfo(journey, i)!.short ? 'text-warn-strong' : 'text-ink-faint'"
                  v-tooltip.top="
                    layoverInfo(journey, i)!.short ? $t('itinerary.agenda.shortLayover') : undefined
                  "
                >
                  <i :class="layoverInfo(journey, i)!.short ? 'mdi mdi-alert-outline' : 'mdi mdi-timer-sand'" />
                  {{ $t('bookings.card.layover') }}: {{ layoverInfo(journey, i)!.text }}
                </span>
              </template>
            </div>
          </template>
          <template v-else>
            <span v-if="booking.origin || booking.destination" class="flex items-center gap-1.5">
              <i :class="BOOKING_TYPE_ICONS[booking.type]" class="text-xs" />
              {{ booking.origin ?? '?' }} → {{ booking.destination ?? '?' }}
            </span>
            <span v-if="booking.start_dt" class="flex items-center gap-1.5">
              <i class="pi pi-calendar text-xs" />
              {{ formatDateTime(booking.start_dt) }}
              <template v-if="booking.end_dt"> → {{ formatDateTime(booking.end_dt) }}</template>
            </span>
          </template>
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
          v-if="(booking.place_id && placeName) || expenseId"
          class="mt-1.5 flex items-center gap-2.5 text-sm"
        >
          <EntityLink
            v-if="booking.place_id && placeName"
            type="place"
            :tripId="trip.id"
            :targetId="booking.place_id"
            :tooltip="$t('bookings.card.placeTooltip', { name: placeName })"
          />
          <EntityLink v-if="expenseId" type="expense" :tripId="trip.id" :targetId="expenseId" />
        </div>
        <p v-if="booking.notes" class="text-sm text-ink-faint mt-1">{{ booking.notes }}</p>
      </div>

      <!-- pagador y "crear gasto": bajo el importe en escritorio, fila propia
           a la derecha en móvil (así no roban ancho al título) -->
      <div
        class="row-start-3 col-span-2 sm:row-start-2 sm:col-start-2 sm:col-span-1 flex flex-col items-end shrink-0"
      >
        <Pill
          v-if="booking.paid_by_common"
          color="warn"
          icon="pi pi-wallet"
          class="mt-0.5"
          v-tooltip.left="$t('bookings.card.paidFromCommon')"
        >
          {{ $t('bookings.card.commonFund') }}
        </Pill>
        <MemberChip v-else-if="payer" :member="payer" class="mt-0.5" />
        <!-- normalmente el gasto nace solo con la reserva; este botón es
             la vía de regeneración (gasto borrado o tasa no disponible) -->
        <Button
          v-if="booking.cost_amount != null && !expenseId"
          :label="$t('bookings.card.createExpense')"
          size="small"
          text
          icon="pi pi-wallet"
          :loading="creatingExpense"
          @click="$emit('create-expense')"
        />
      </div>
    </div>
    <div class="mt-3 pt-3 border-t border-line-subtle">
      <AttachmentList :bookingId="booking.id" />
    </div>
  </div>
</template>
