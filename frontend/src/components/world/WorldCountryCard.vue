<script setup lang="ts">
import { ref } from 'vue'
import Button from 'primevue/button'
import ImageZoom from '../ui/ImageZoom.vue'
import Pill from '../ui/Pill.vue'
import type { WorldPlace } from '../../api/types'
import { countryName, flagEmoji } from '../../countries'
import { visitedLabel } from '../../utils/worldGrouping'
import { focusStyle } from '../../utils/imageFocus'
import type { CountryState } from '../../utils/worldChoropleth'

// Ficha del país tocado en el mapa: flota sobre el mapa en vez de ir en un
// popup de Leaflet — así es un componente Vue normal (tokens, i18n, tamaños) y
// en móvil ocupa el ancho de la tarjeta en lugar de un globo diminuto.
defineProps<{
  code: string
  state: CountryState
  /** entrada del diario, si el país está guardado (puede faltar: ciudad suelta) */
  place: WorldPlace | null
  /** el país tiene ciudades o sitios dentro: no se puede quitar (409 del backend) */
  locked: boolean
}>()

defineEmits<{ close: []; edit: []; remove: [] }>()

// la postal se ve recortada en la ficha: al tocarla vuela a tamaño grande, el
// mismo zoom que la postal del diario
const zoom = ref<InstanceType<typeof ImageZoom> | null>(null)
</script>

<template>
  <div
    class="tt-pop-in absolute inset-x-3 bottom-3 z-map-overlay sm:inset-x-auto sm:left-3 sm:w-72"
  >
    <div class="bg-surface border border-line rounded-card shadow-lift p-3">
      <div class="flex items-start gap-2">
        <span class="text-2xl leading-none">{{ flagEmoji(code) }}</span>
        <div class="min-w-0 flex-1">
          <div class="font-semibold text-ink truncate">{{ countryName(code) }}</div>
          <div class="flex flex-wrap items-center gap-x-2 gap-y-1 mt-0.5 text-xs text-ink-muted">
            <span v-if="place && visitedLabel(place)">
              <i class="pi pi-calendar text-2xs" /> {{ visitedLabel(place) }}
            </span>
            <span v-if="state.regions">
              {{ $t('world.map.regionCount', { n: state.regions }, state.regions) }}
            </span>
            <span v-if="state.cities">
              {{ $t('world.map.cityCount', { n: state.cities }, state.cities) }}
            </span>
          </div>
        </div>
        <Button
          icon="pi pi-times"
          severity="secondary"
          text
          size="small"
          class="-mr-1.5 -mt-1.5"
          :aria-label="$t('common.actions.close')"
          @click="$emit('close')"
        />
      </div>

      <button
        v-if="place?.photo_url"
        type="button"
        class="block w-full mt-2 rounded-lg overflow-hidden cursor-zoom-in"
        :aria-label="$t('world.form.photo')"
        @click="zoom?.openFrom($event.currentTarget as HTMLElement)"
      >
        <img
          :src="place.photo_url"
          class="w-full h-24 object-cover"
          :style="{ objectPosition: focusStyle(place.photo_focus_x, place.photo_focus_y) }"
          alt=""
        />
      </button>
      <p v-if="place?.note" class="mt-2 text-xs text-ink-muted whitespace-pre-wrap">
        {{ place.note }}
      </p>
      <Pill v-if="place?.origin" color="info" class="mt-2">
        {{ $t('world.map.tripOrigin', { origin: place.origin }) }}
      </Pill>

      <div v-if="place" class="flex flex-wrap items-center gap-2 mt-3">
        <Button
          :label="$t('common.actions.edit')"
          icon="pi pi-pencil"
          size="small"
          outlined
          severity="secondary"
          @click="$emit('edit')"
        />
        <Button
          :label="$t('world.confirmRemove.accept')"
          icon="pi pi-trash"
          size="small"
          text
          severity="danger"
          :disabled="locked"
          v-tooltip.top="locked ? $t('world.list.countryLocked') : undefined"
          @click="$emit('remove')"
        />
      </div>
    </div>

    <ImageZoom ref="zoom" :src="place?.photo_url ?? null" :alt="countryName(code)" />
  </div>
</template>
