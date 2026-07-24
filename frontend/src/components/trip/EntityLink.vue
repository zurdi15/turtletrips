<script setup lang="ts">
import { computed } from 'vue'

type EntityType = 'place' | 'booking' | 'expense'

const props = withDefaults(
  defineProps<{
    type: EntityType
    tripId: number
    targetId: number
    /** tooltip específico ("Sitio: Fushimi Inari"); si no, el genérico del tipo */
    tooltip?: string
    /** hereda el color del texto (chips dentro de bandas coloreadas) */
    inheritColor?: boolean
    /** atenuado hasta pasar el ratón (el chip "volver a la reserva" de las bandas) */
    dimmed?: boolean
    /** tamaño del icono */
    size?: 'xs' | '2xs'
  }>(),
  { inheritColor: false, dimmed: false, size: 'xs' },
)

// enlaces cruzados sitio/reserva/gasto: cada tipo lleva su pestaña, su query
// de highlight, su icono y su color de dominio
const META: Record<EntityType, { route: string; query: string; icon: string; color: string; tooltip: string }> = {
  place: {
    route: 'trip-places',
    query: 'place',
    icon: 'pi pi-map-marker',
    color: 'text-brand',
    tooltip: 'Ver sitio',
  },
  booking: {
    route: 'trip-bookings',
    query: 'booking',
    icon: 'pi pi-ticket',
    color: 'text-lodging',
    tooltip: 'Ver reserva',
  },
  expense: {
    route: 'trip-expenses',
    query: 'expense',
    icon: 'pi pi-wallet',
    color: 'text-warn',
    tooltip: 'Ver gasto',
  },
}

const meta = computed(() => META[props.type])
const to = computed(() => ({
  name: meta.value.route,
  params: { id: props.tripId },
  query: { [meta.value.query]: props.targetId },
}))
</script>

<template>
  <router-link
    :to="to"
    class="no-underline"
    :class="[inheritColor ? 'text-inherit' : meta.color, dimmed ? 'opacity-50 hover:opacity-100' : '']"
    v-tooltip.top="tooltip ?? meta.tooltip"
    @click.stop
  >
    <i :class="[meta.icon, size === '2xs' ? 'text-2xs' : 'text-xs']" />
  </router-link>
</template>
