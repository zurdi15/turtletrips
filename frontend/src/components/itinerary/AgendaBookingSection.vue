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
  /** nombre de la reserva: tooltip de sus chips cuando la banda lleva varias */
  bookingTitle: string
  placeId: number | null
  expenseId: number | null
  /** el chip de gasto hereda el color (banda ámbar: ámbar sobre ámbar no se ve) */
  expenseInherit?: boolean
  /** transporte: tipo, horas y ruta por separado, cada uno con su tipografía
   *  (si está, head/label se ignoran) */
  transport?: TransportRowView
}
</script>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import EntityLink from '../trip/EntityLink.vue'

// UNA banda para las tres secciones clonadas de la agenda: transporte (azul,
// arriba), otras reservas (ámbar, arriba) y alojamiento (violeta, al pie)
const props = withDefaults(
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

const { t } = useI18n()

// chips de sitio/gasto/reserva: van en la cabecera de la banda, UN grupo por
// reserva (un vuelo con escalas son varias filas y una sola reserva). Al pie
// de cada fila bajaban en móvil a una línea propia y partían el bloque
const chipGroups = computed(() => {
  const groups = new Map<number, Pick<AgendaRow, 'bookingId' | 'bookingTitle' | 'placeId' | 'expenseId' | 'expenseInherit'>>()
  for (const row of props.rows) {
    const group = groups.get(row.bookingId)
    if (!group) {
      groups.set(row.bookingId, { ...row })
      continue
    }
    group.placeId ??= row.placeId
    group.expenseId ??= row.expenseId
  }
  return [...groups.values()]
})

// con varias reservas en la banda cada chip dice de cuál es
function chipTooltip(key: string, group: { bookingTitle: string }): string | undefined {
  return chipGroups.value.length > 1 ? `${t(key)}: ${group.bookingTitle}` : undefined
}

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
    <div
      class="px-4 pb-0.5 flex items-center gap-1.5"
      :class="TONE_CLASSES[tone].header"
    >
      <p class="text-2xs font-semibold uppercase tracking-wide flex items-center gap-1.5">
        <i :class="icon" /> {{ title }}
      </p>
      <!-- chips de cada reserva, con aire: separados del título y entre sí,
           y un filete entre reservas si la banda lleva varias -->
      <div class="flex flex-wrap items-center gap-x-4 gap-y-1 ml-4">
        <span
          v-for="(group, i) in chipGroups"
          :key="group.bookingId"
          class="flex items-center gap-3.5"
        >
          <span v-if="i > 0" class="w-px h-3 mr-0.5 bg-current opacity-25" />
          <EntityLink
            v-if="group.placeId"
            type="place"
            :tripId="tripId"
            :targetId="group.placeId"
            :tooltip="chipTooltip('common.entityLink.viewPlace', group)"
            size="2xs"
          />
          <EntityLink
            v-if="group.expenseId"
            type="expense"
            :tripId="tripId"
            :targetId="group.expenseId"
            :inheritColor="group.expenseInherit"
            :tooltip="chipTooltip('common.entityLink.viewExpense', group)"
            size="2xs"
          />
          <EntityLink
            type="booking"
            :tripId="tripId"
            :targetId="group.bookingId"
            :tooltip="chipTooltip('common.entityLink.viewBooking', group)"
            inheritColor
            dimmed
            size="2xs"
          />
        </span>
      </div>
    </div>
    <div
      v-for="row in rows"
      :key="row.key"
      class="flex items-center gap-x-3 px-4 py-1"
      :class="TONE_CLASSES[tone].row"
    >
      <!-- transporte: columna fija (alinea horas y rutas entre filas); el resto
           ("Check-out: 10:00") crece antes que recortarse en móvil -->
      <span
        class="text-xs sm:text-sm shrink-0"
        :class="[
          row.transport ? 'w-24 sm:w-28 truncate' : 'min-w-24 sm:min-w-28 whitespace-nowrap',
          row.transport?.layover ? 'opacity-60' : 'opacity-80',
        ]"
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
          class="flex-1 min-w-0 truncate no-underline hover:underline"
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
        class="flex-1 min-w-0 font-medium text-sm truncate text-inherit no-underline hover:underline"
      >
        {{ row.label }}
      </router-link>
    </div>
  </div>
</template>
