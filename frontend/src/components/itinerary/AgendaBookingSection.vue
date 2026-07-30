<script lang="ts">
import type { TransportRowView } from '../../utils/itinerary'

/** Fila derivada de una reserva para las bandas de la agenda. */
export interface AgendaRow {
  key: string
  /** cabecera de la columna izquierda: "Vuelo: 07:30", "Check-in: 15:00"… */
  head: string
  /** texto del enlace: ruta MAD → NRT o título de la reserva */
  label: string
  bookingId: number
  placeId: number | null
  expenseId: number | null
  /** el chip de gasto hereda el color (banda ámbar: ámbar sobre ámbar no se ve) */
  expenseInherit?: boolean
  /** sin chips: los tramos de un trayecto los llevan una sola vez (la primera
   *  fila); el label sigue enlazando a la reserva */
  hideChips?: boolean
  /** transporte: tipo, horas y ruta por separado, cada uno con su tipografía
   *  (si está, head/label se ignoran) */
  transport?: TransportRowView
}
</script>

<script setup lang="ts">
import EntityLink from '../trip/EntityLink.vue'

// UNA banda para las tres secciones clonadas de la agenda: transporte (azul,
// arriba), otras reservas (ámbar, arriba) y alojamiento (violeta, al pie)
withDefaults(
  defineProps<{
    tone: 'info' | 'warn' | 'lodging'
    title: string
    icon: string
    tripId: number
    rows: AgendaRow[]
    /** posición dentro de la tarjeta del día: arriba (border-b) o al pie (border-t) */
    position?: 'top' | 'bottom'
  }>(),
  { position: 'top' },
)

const TONE_CLASSES: Record<string, { band: string; header: string; row: string }> = {
  info: { band: 'bg-info-tint-strong', header: 'text-info', row: 'text-info-strong' },
  warn: { band: 'bg-warn-tint-strong', header: 'text-warn', row: 'text-warn-strong' },
  lodging: { band: 'bg-lodging-tint-strong', header: 'text-lodging', row: 'text-lodging-strong' },
}
</script>

<template>
  <div
    class="py-1.5"
    :class="[TONE_CLASSES[tone].band, position === 'bottom' ? 'border-t border-line-subtle' : 'border-b border-line-subtle']"
  >
    <p
      class="px-4 pb-0.5 text-2xs font-semibold uppercase tracking-wide flex items-center gap-1.5"
      :class="TONE_CLASSES[tone].header"
    >
      <i :class="icon" /> {{ title }}
    </p>
    <div
      v-for="row in rows"
      :key="row.key"
      class="flex items-center gap-3 px-4 py-1"
      :class="TONE_CLASSES[tone].row"
    >
      <span
        class="text-xs sm:text-sm w-24 sm:w-28 shrink-0 truncate"
        :class="row.transport?.layover ? 'opacity-60' : 'opacity-80'"
      >
        {{ row.transport ? row.transport.kind : row.head }}
      </span>
      <!-- transporte: horas en columna propia (salida–llegada, +n si cruza
           noches), ruta como enlace y número de vuelo aparte -->
      <template v-if="row.transport">
        <span class="w-24 sm:w-28 shrink-0 tabular-nums text-xs sm:text-sm font-semibold whitespace-nowrap">
          <template v-if="row.transport.dep || row.transport.arr">
            {{ row.transport.dep ?? '' }}<span v-if="row.transport.dep && row.transport.arr" class="opacity-40">–</span>{{ row.transport.arr ?? '' }}<sup v-if="row.transport.arr && row.transport.plusDays" class="text-3xs font-normal opacity-70">+{{ row.transport.plusDays }}</sup>
          </template>
        </span>
        <router-link
          :to="{ name: 'trip-bookings', params: { id: tripId }, query: { booking: row.bookingId } }"
          class="truncate no-underline hover:underline"
          :class="
            row.transport.layover
              ? row.transport.shortLayover
                ? 'text-xs font-medium text-warn-strong'
                : 'text-xs opacity-70 text-inherit'
              : 'font-medium text-sm text-inherit'
          "
        >
          <i
            v-if="row.transport.shortLayover"
            class="mdi mdi-alert-outline text-2xs"
            v-tooltip.top="$t('itinerary.agenda.shortLayover')"
          />
          {{ row.transport.route }}
        </router-link>
        <span
          v-if="row.transport.flightNumber"
          class="font-mono text-2xs opacity-60 shrink-0 hidden sm:inline"
        >
          {{ row.transport.flightNumber }}
        </span>
      </template>
      <router-link
        v-else
        :to="{ name: 'trip-bookings', params: { id: tripId }, query: { booking: row.bookingId } }"
        class="font-medium text-sm truncate text-inherit no-underline hover:underline"
      >
        {{ row.label }}
      </router-link>
      <span v-if="!row.hideChips" class="ml-auto flex items-center gap-2.5 shrink-0">
        <EntityLink
          v-if="row.placeId"
          type="place"
          :tripId="tripId"
          :targetId="row.placeId"
          size="2xs"
        />
        <EntityLink
          v-if="row.expenseId"
          type="expense"
          :tripId="tripId"
          :targetId="row.expenseId"
          :inheritColor="row.expenseInherit"
          size="2xs"
        />
        <EntityLink
          type="booking"
          :tripId="tripId"
          :targetId="row.bookingId"
          inheritColor
          dimmed
          size="2xs"
        />
      </span>
    </div>
  </div>
</template>
