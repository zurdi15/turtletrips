<script setup lang="ts">
import { computed } from 'vue'
import EmptyState from '../EmptyState.vue'
import type { WorldPlace } from '../../api/types'
import { countryName, flagEmoji } from '../../countries'
import { intlLocale } from '../../i18n'
import {
  KIND_COLORS,
  KIND_KEYS,
  displayName,
  type TimelineSegment,
} from '../../utils/worldGrouping'

// Historia viajera: los años como hitos de una línea vertical y sus destinos
// colgando; clic en un destino → verlo en el mapa. Con filtros activos, lo que
// se oculta deja un hueco "⋯" para que la línea no mienta sobre lo que hubo.
const props = defineProps<{ segments: TimelineSegment[] }>()
defineEmits<{ 'fly-to': [place: WorldPlace] }>()

function monthLabel(place: WorldPlace): string | null {
  if (place.visited_month == null) return null
  return new Date(2000, place.visited_month - 1, 1).toLocaleDateString(intlLocale(), {
    month: 'long',
  })
}

// países que presiden cada año; sus ciudades no repiten el nombre del país
const countryCodesByYear = computed(() => {
  const map = new Map<number, Set<string>>()
  for (const segment of props.segments) {
    if (segment.type !== 'year') continue
    map.set(
      segment.year,
      new Set(
        segment.entries
          .filter((e) => e.kind === 'country' && e.country_code)
          .map((e) => e.country_code as string),
      ),
    )
  }
  return map
})

/** solo se etiqueta el país de una ciudad si ese año no lo lleva ya delante */
function showsCountry(year: number, place: WorldPlace): boolean {
  if (place.kind === 'country' || !place.country_code) return false
  return !countryCodesByYear.value.get(year)?.has(place.country_code)
}
</script>

<template>
  <EmptyState
    v-if="!segments.length"
    icon="pi pi-history"
    :title="$t('world.timeline.emptyTitle')"
    :subtitle="$t('world.timeline.emptySubtitle')"
  />

  <div v-else class="tt-stagger max-w-2xl">
    <template v-for="(segment, index) in segments" :key="segment.type === 'year' ? segment.year : `gap-${index}`">
      <!-- año visible -->
      <section v-if="segment.type === 'year'" class="relative pl-8 pb-6 last:pb-0">
        <!-- la línea del tiempo: continua entre años, con nodo por año -->
        <span class="absolute left-2.5 top-1 bottom-0 w-px bg-line" aria-hidden="true" />
        <span
          class="absolute left-0 top-0.5 w-5 h-5 rounded-full bg-brand-tint border-2 border-primary"
          aria-hidden="true"
        />
        <div class="flex items-baseline gap-2 flex-wrap">
          <h3 class="text-lg font-bold text-ink-heading tabular-nums leading-6">{{ segment.year }}</h3>
          <span v-if="segment.hidden" class="text-xs text-ink-faint">
            {{ $t('world.timeline.hiddenInYear', { n: segment.hidden }, segment.hidden) }}
          </span>
        </div>

        <ul class="mt-2 flex flex-col gap-1.5">
          <li v-for="place in segment.entries" :key="place.id">
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
              <!-- el país solo cuando no preside ya ese año (filtrado por tipo,
                   o país fechado en otro año): si no, sería redundante -->
              <span v-if="showsCountry(segment.year, place)" class="text-xs text-ink-faint shrink-0">
                {{ flagEmoji(place.country_code!) }} {{ countryName(place.country_code!) }}
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

      <!-- hueco: años enteros que los filtros dejan fuera. El tramo ES la línea
           punteada (nada continuo por detrás): la línea "se interrumpe" ahí -->
      <div v-else class="relative pl-8 pb-6">
        <span class="tt-timeline-gap absolute left-2.5 top-0 bottom-0" aria-hidden="true" />
        <p class="text-xs text-ink-faint pt-1">
          {{ $t('world.timeline.hiddenGap', { n: segment.hidden }, segment.hidden) }}
        </p>
      </div>
    </template>
  </div>
</template>

<style scoped>
/* el tramo filtrado continúa la línea del tiempo en punteado; el borde de 2px
   se recentra sobre el eje de la línea continua (1px) con el translate */
.tt-timeline-gap {
  width: 0;
  border-left: 2px dotted var(--tt-line-strong);
  transform: translateX(-0.5px);
}
</style>
