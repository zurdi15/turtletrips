<script setup lang="ts">
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

defineProps<{
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
    <div class="flex items-start gap-3">
      <!-- izquierda: título y detalles (encoge y trunca, nunca empuja las acciones) -->
      <div class="min-w-0 flex-1">
        <div class="flex items-center gap-2 flex-wrap">
          <h3 class="font-semibold text-ink-heading">{{ booking.title }}</h3>
          <span v-if="booking.provider" class="text-sm text-ink-faint">
            · {{ booking.provider }}
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

      <!-- derecha: importe + acciones en una línea, y el gasto debajo -->
      <div class="flex flex-col items-end shrink-0">
        <div class="flex items-center gap-1">
          <span
            v-if="booking.cost_amount != null"
            class="font-semibold text-ink-heading mr-1.5 whitespace-nowrap"
          >
            {{ formatMoney(booking.cost_amount, booking.cost_currency ?? trip.base_currency) }}
          </span>
          <RowActions always @edit="$emit('edit')" @remove="$emit('remove')" />
        </div>
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
