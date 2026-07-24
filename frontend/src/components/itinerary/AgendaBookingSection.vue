<script lang="ts">
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
      <span class="text-xs sm:text-sm w-24 sm:w-28 shrink-0 opacity-80 truncate">
        {{ row.head }}
      </span>
      <router-link
        :to="{ name: 'trip-bookings', params: { id: tripId }, query: { booking: row.bookingId } }"
        class="font-medium text-sm truncate text-inherit no-underline hover:underline"
      >
        {{ row.label }}
      </router-link>
      <span class="ml-auto flex items-center gap-2.5 shrink-0">
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
