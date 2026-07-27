<script setup lang="ts">
import EmptyState from '../EmptyState.vue'
import type { WorldPlace } from '../../api/types'
import { flagEmoji } from '../../countries'
import { intlLocale } from '../../i18n'
import {
  KIND_COLORS,
  KIND_KEYS,
  displayName,
  type TimelineYear,
} from '../../utils/worldGrouping'

// Historia viajera: los años como hitos de una línea vertical y sus destinos
// colgando; clic en un destino → verlo en el mapa
defineProps<{ years: TimelineYear[] }>()
defineEmits<{ 'fly-to': [place: WorldPlace] }>()

function monthLabel(place: WorldPlace): string | null {
  if (place.visited_month == null) return null
  return new Date(2000, place.visited_month - 1, 1).toLocaleDateString(intlLocale(), {
    month: 'long',
  })
}
</script>

<template>
  <EmptyState
    v-if="!years.length"
    icon="pi pi-history"
    :title="$t('world.timeline.emptyTitle')"
    :subtitle="$t('world.timeline.emptySubtitle')"
  />

  <div v-else class="tt-stagger max-w-2xl">
    <section v-for="group in years" :key="group.year" class="relative pl-8 pb-6 last:pb-0">
      <!-- la línea del tiempo: continua entre años, con nodo por año -->
      <span class="absolute left-2.5 top-1 bottom-0 w-px bg-line" aria-hidden="true" />
      <span
        class="absolute left-0 top-0.5 w-5 h-5 rounded-full bg-brand-tint border-2 border-primary"
        aria-hidden="true"
      />
      <h3 class="text-lg font-bold text-ink-heading tabular-nums leading-6">{{ group.year }}</h3>

      <ul class="mt-2 flex flex-col gap-1.5">
        <li v-for="place in group.entries" :key="place.id">
          <button
            type="button"
            class="w-full flex items-center gap-2.5 text-left rounded-lg px-2.5 py-1.5 -ml-2.5 hover:bg-surface-hover cursor-pointer"
            @click="$emit('fly-to', place)"
          >
            <!-- bandera para países; dot de tipo para ciudades/sitios -->
            <span v-if="place.kind === 'country'" class="text-xl leading-none">
              {{ place.country_code ? flagEmoji(place.country_code) : '🌐' }}
            </span>
            <span
              v-else
              class="w-2.5 h-2.5 rounded-full shrink-0 ml-1.5 mr-1"
              :style="{ background: KIND_COLORS[place.kind] }"
              v-tooltip.left="$t(KIND_KEYS[place.kind])"
            />
            <span
              class="min-w-0 truncate"
              :class="place.kind === 'country' ? 'font-semibold text-ink' : 'text-sm text-ink-secondary'"
            >
              {{ displayName(place) }}
            </span>
            <span v-if="monthLabel(place)" class="text-xs text-ink-faint capitalize shrink-0">
              {{ monthLabel(place) }}
            </span>
            <span class="flex-1" />
            <span v-if="place.origin" class="text-xs text-ink-faint truncate max-w-40">
              {{ $t('world.list.tripOrigin', { origin: place.origin }) }}
            </span>
          </button>
        </li>
      </ul>
    </section>
  </div>
</template>
