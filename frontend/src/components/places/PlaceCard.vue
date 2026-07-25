<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import RowActions from '../ui/RowActions.vue'
import EntityLink from '../trip/EntityLink.vue'
import type { Booking, Expense, Place } from '../../api/types'
import { PLACE_CATEGORY_ICONS, PLACE_CATEGORY_KEYS } from '../../constants'
import { PLACE_CATEGORY_COLORS } from '../../theme'
import { formatMoney } from '../../composables/useMoney'

const { t } = useI18n()

defineProps<{
  place: Place
  tripId: number
  /** reservas y gastos enlazados a este sitio (chips a otras pestañas) */
  bookings: Booking[]
  expenses: Expense[]
  baseCurrency: string
  selected: boolean
}>()
defineEmits<{ select: []; edit: []; remove: []; 'toggle-visited': [] }>()
</script>

<template>
  <div
    class="tt-lift bg-surface rounded-card border p-3 cursor-pointer"
    :class="
      selected
        ? 'border-primary ring-1 ring-primary'
        : 'border-line hover:border-line-strong'
    "
    @click="$emit('select')"
  >
    <div class="flex items-start gap-3">
      <!-- visitado: anillo verde en el icono (sin tachar el nombre) -->
      <span
        class="w-9 h-9 rounded-full flex items-center justify-center shrink-0 text-white"
        :class="{ 'ring-2 ring-emerald-400': place.visited }"
        :style="{ background: PLACE_CATEGORY_COLORS[place.category] }"
      >
        <i :class="PLACE_CATEGORY_ICONS[place.category]" class="text-sm" />
      </span>
      <div class="flex-1 min-w-0">
        <!-- min-h igual al icono (h-9): el nombre queda centrado a su altura -->
        <div class="flex items-center gap-2 flex-wrap min-h-9">
          <span class="font-medium">{{ place.name }}</span>
          <i
            v-if="place.priority > 0"
            class="pi pi-star-fill text-amber-400 text-xs"
            v-tooltip.top="t('places.mustSee')"
          />
          <Tag
            :value="t(PLACE_CATEGORY_KEYS[place.category])"
            :style="{
              background: `${PLACE_CATEGORY_COLORS[place.category]}20`,
              color: PLACE_CATEGORY_COLORS[place.category],
            }"
            class="text-xs"
          />
          <!-- enlaces compactos a reserva y gasto: van agrupados para que
               en móvil salten de línea juntos, nunca separados -->
          <span v-if="bookings.length || expenses.length" class="flex items-center gap-2.5">
            <EntityLink
              v-for="b in bookings"
              :key="`bk-${b.id}`"
              type="booking"
              :tripId="tripId"
              :targetId="b.id"
              :tooltip="t('places.card.bookingTooltip', { title: b.title })"
            />
            <EntityLink
              v-for="e in expenses"
              :key="`ex-${e.id}`"
              type="expense"
              :tripId="tripId"
              :targetId="e.id"
              :tooltip="
                t('places.card.expenseTooltip', {
                  description: e.description,
                  amount: formatMoney(e.amount_base, baseCurrency),
                })
              "
            />
          </span>
        </div>
        <p v-if="place.notes" class="text-sm text-ink-muted mt-0.5 truncate">{{ place.notes }}</p>
        <a
          v-if="place.url"
          :href="place.url"
          target="_blank"
          rel="noopener"
          class="text-xs text-info hover:underline"
          @click.stop
        >
          <i class="pi pi-external-link text-3xs" /> {{ t('places.card.link') }}
        </a>
      </div>
      <!-- .stop: las acciones no deben seleccionar la tarjeta -->
      <span class="shrink-0" @click.stop>
        <RowActions always @edit="$emit('edit')" @remove="$emit('remove')">
          <template #before>
            <Button
              :icon="place.visited ? 'pi pi-check-circle' : 'pi pi-circle'"
              :severity="place.visited ? 'success' : 'secondary'"
              text
              size="small"
              v-tooltip.top="
                place.visited ? t('places.card.markPending') : t('places.card.markVisited')
              "
              @click="$emit('toggle-visited')"
            />
          </template>
        </RowActions>
      </span>
    </div>
  </div>
</template>
