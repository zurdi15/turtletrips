<script setup lang="ts">
import AutoComplete from 'primevue/autocomplete'
import Button from 'primevue/button'
import CountrySelect from '../ui/CountrySelect.vue'
import type { GeocodeResult } from '../../api/types'
import { useGeocodeSearch } from '../../composables/useGeocode'

// Alta al diario: buscador de ciudades/sitios y selector de países. Visible en
// TODAS las vistas del mapa, porque las estadísticas también se alimentan aquí.
defineProps<{
  /** países ya marcados: no vuelven a ofrecerse */
  markedCountryCodes: string[]
  adding: boolean
}>()

const emit = defineEmits<{ 'geocode-select': [result: GeocodeResult]; add: [] }>()

/** el padre conserva la selección de los que fallaron, así que el modelo es suyo */
const codes = defineModel<string[]>('codes', { required: true })

const { results: geoResults, search: geoSearch } = useGeocodeSearch()
const searchValue = defineModel<string | GeocodeResult>('search', { required: true })

function onSelect(event: { value: GeocodeResult }) {
  emit('geocode-select', event.value)
  searchValue.value = ''
}
</script>

<template>
  <div class="flex flex-wrap items-center gap-2 mb-3">
    <AutoComplete
      v-model="searchValue"
      :suggestions="geoResults"
      optionLabel="display_name"
      :placeholder="$t('world.search.placePlaceholder')"
      class="w-full sm:w-80 [&_input]:w-full"
      @complete="(e) => geoSearch(e.query)"
      @item-select="onSelect"
    />
    <CountrySelect
      v-model="codes"
      multiple
      :exclude="markedCountryCodes"
      :placeholder="$t('world.search.countryPlaceholder')"
      :disabled="adding"
      class="w-full sm:w-80"
    />
    <Button
      v-if="codes.length"
      class="tt-pop-in max-sm:w-full"
      icon="pi pi-plus"
      :label="$t('world.search.addCountries', { n: codes.length }, codes.length)"
      :loading="adding"
      @click="emit('add')"
    />
  </div>
</template>
