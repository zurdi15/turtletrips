<script setup lang="ts">
import { ref } from 'vue'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Textarea from 'primevue/textarea'
import Select from 'primevue/select'
import AutoComplete from 'primevue/autocomplete'
import Checkbox from 'primevue/checkbox'
import FormDialog from './ui/FormDialog.vue'
import FormField from './ui/FormField.vue'
import type { GeocodeResult, Place, PlaceCategory } from '../api/types'
import { PLACE_CATEGORY_LABELS, toSelectOptions } from '../constants'
import { usePlacesStore } from '../stores/places'
import { useFormDialog } from '../composables/useFormDialog'
import { useGeocodeSearch } from '../composables/useGeocode'

const props = defineProps<{ place?: Place | null }>()
const visible = defineModel<boolean>('visible', { required: true })
const emit = defineEmits<{ saved: [] }>()

const store = usePlacesStore()
const { results, search } = useGeocodeSearch()

const name = ref('')
const category = ref<PlaceCategory>('sight')
const geocodeQuery = ref<string | GeocodeResult>('')
const address = ref('')
const lat = ref<number | null>(null)
const lon = ref<number | null>(null)
const url = ref('')
const notes = ref('')
const mustSee = ref(false)
const visited = ref(false)

const categoryOptions = toSelectOptions(PLACE_CATEGORY_LABELS)

const { saving, save } = useFormDialog({
  visible,
  entity: () => props.place,
  reset(p) {
    name.value = p?.name ?? ''
    category.value = p?.category ?? 'sight'
    address.value = p?.address ?? ''
    geocodeQuery.value = p?.address ?? ''
    lat.value = p?.lat ?? null
    lon.value = p?.lon ?? null
    url.value = p?.url ?? ''
    notes.value = p?.notes ?? ''
    mustSee.value = (p?.priority ?? 0) > 0
    visited.value = p?.visited ?? false
  },
  validate: () => (name.value.trim() ? null : 'El nombre es obligatorio'),
  submit() {
    const payload = {
      name: name.value.trim(),
      category: category.value,
      address: address.value || null,
      lat: lat.value,
      lon: lon.value,
      url: url.value || null,
      notes: notes.value || null,
      priority: mustSee.value ? 1 : 0,
      visited: visited.value,
    }
    return props.place ? store.update(props.place.id, payload) : store.create(payload)
  },
  onSaved: () => emit('saved'),
})

function onGeocodeSelect(event: { value: GeocodeResult }) {
  const r = event.value
  address.value = r.display_name
  lat.value = r.lat
  lon.value = r.lon
  // el nombre se autorellena con el del sitio; se puede editar después
  name.value = r.display_name.split(',')[0].trim()
}
</script>

<template>
  <FormDialog
    v-model:visible="visible"
    :header="place ? 'Editar sitio' : 'Nuevo sitio'"
    :saving="saving"
    :saveLabel="place ? 'Guardar' : 'Añadir sitio'"
    @save="save"
  >
    <FormField label="Ubicación">
      <AutoComplete
        v-model="geocodeQuery"
        :suggestions="results"
        optionLabel="display_name"
        placeholder="Busca un lugar o dirección…"
        fluid
        autofocus
        @complete="(e) => search(e.query)"
        @item-select="onGeocodeSelect"
      />
      <template #hint>
        <p v-if="lat != null && lon != null" class="text-xs text-ink-faint">
          <i class="pi pi-map-marker text-3xs" /> {{ lat.toFixed(5) }}, {{ lon.toFixed(5) }}
        </p>
      </template>
    </FormField>

    <div class="grid grid-cols-2 gap-3">
      <FormField label="Nombre" required>
        <InputText v-model="name" placeholder="Fushimi Inari" />
      </FormField>
      <FormField label="Categoría">
        <Select
          v-model="category"
          :options="categoryOptions"
          optionLabel="label"
          optionValue="value"
        />
      </FormField>
    </div>

    <div class="grid grid-cols-2 gap-3">
      <FormField label="Latitud">
        <InputNumber v-model="lat" :minFractionDigits="0" :maxFractionDigits="6" locale="en-US" />
      </FormField>
      <FormField label="Longitud">
        <InputNumber v-model="lon" :minFractionDigits="0" :maxFractionDigits="6" locale="en-US" />
      </FormField>
    </div>

    <FormField label="Enlace">
      <InputText v-model="url" placeholder="https://…" />
    </FormField>
    <FormField label="Notas">
      <Textarea v-model="notes" rows="2" autoResize />
    </FormField>
    <div class="flex items-center gap-6">
      <label class="flex items-center gap-2 text-sm">
        <Checkbox v-model="mustSee" binary /> Imprescindible
        <i class="pi pi-star-fill text-amber-400 text-xs" />
      </label>
      <label class="flex items-center gap-2 text-sm">
        <Checkbox v-model="visited" binary /> Visitado
      </label>
    </div>
  </FormDialog>
</template>
