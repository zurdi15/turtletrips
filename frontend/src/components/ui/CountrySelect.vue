<script setup lang="ts" generic="T extends string[] | string | null">
import { computed } from 'vue'
import Select from 'primevue/select'
import MultiSelect from 'primevue/multiselect'
import { countryOptions } from '../../countries'

// Selector de países ÚNICO de la app: mismo listado (bandera + nombre en el
// idioma activo, ordenado por locale), buscador y scroller virtual en todos los
// sitios donde se eligen países. `multiple` decide entre chips o desplegable.
// La cabecera lleva SOLO el buscador: marcar los ~200 países de golpe no
// significa nada en ningún sitio donde se usa (de ahí showToggleAll=false).
const props = withDefaults(
  defineProps<{
    /** varios países (chips) en vez de uno solo */
    multiple?: boolean
    /** limitar el listado a estos códigos (p. ej. los que ya hay en el diario) */
    codes?: string[] | null
    /** ocultar estos códigos (p. ej. los países ya marcados) */
    exclude?: string[] | null
    /** primera opción sin país concreto ("Sin país", "Todos los países") */
    emptyOption?: { value: string | null; label: string } | null
    /** 'chip' pinta cada país seleccionado como chip; 'comma' los lista */
    display?: 'chip' | 'comma'
    placeholder?: string
    maxSelectedLabels?: number
    loading?: boolean
    disabled?: boolean
  }>(),
  {
    multiple: false,
    codes: null,
    exclude: null,
    emptyOption: null,
    display: 'chip',
    placeholder: undefined,
    maxSelectedLabels: 6,
    loading: false,
    disabled: false,
  },
)

const model = defineModel<T>({ required: true })

const options = computed(() => {
  const excluded = new Set(props.exclude ?? [])
  const allowed = props.codes ? new Set(props.codes) : null
  const list = countryOptions()
    .filter((o) => !excluded.has(o.code) && (!allowed || allowed.has(o.code)))
    .map((o) => ({ value: o.code as string | null, label: o.label }))
  return props.emptyOption ? [props.emptyOption, ...list] : list
})
</script>

<template>
  <MultiSelect
    v-if="multiple"
    v-model="model"
    :options="options"
    optionLabel="label"
    optionValue="value"
    filter
    :showToggleAll="false"
    :display="display"
    :placeholder="placeholder"
    :maxSelectedLabels="maxSelectedLabels"
    :loading="loading"
    :disabled="disabled"
    :virtualScrollerOptions="{ itemSize: 38 }"
  />
  <Select
    v-else
    v-model="model"
    :options="options"
    optionLabel="label"
    optionValue="value"
    filter
    :placeholder="placeholder"
    :loading="loading"
    :disabled="disabled"
    :virtualScrollerOptions="{ itemSize: 38 }"
  />
</template>
