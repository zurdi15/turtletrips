<script setup lang="ts">
import { ref, watch } from 'vue'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Textarea from 'primevue/textarea'
import Select from 'primevue/select'
import AutoComplete from 'primevue/autocomplete'
import Checkbox from 'primevue/checkbox'
import Button from 'primevue/button'
import { useToast } from 'primevue/usetoast'
import type { GeocodeResult, Place, PlaceCategory } from '../api/types'
import { PLACE_CATEGORY_LABELS, toSelectOptions } from '../constants'
import { usePlacesStore } from '../stores/places'
import { useGeocodeSearch } from '../composables/useGeocode'

const props = defineProps<{ place?: Place | null }>()
const visible = defineModel<boolean>('visible', { required: true })
const emit = defineEmits<{ saved: [] }>()

const toast = useToast()
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
const saving = ref(false)

const categoryOptions = toSelectOptions(PLACE_CATEGORY_LABELS)

watch(visible, (open) => {
  if (!open) return
  const p = props.place
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
})

function onGeocodeSelect(event: { value: GeocodeResult }) {
  const r = event.value
  address.value = r.display_name
  lat.value = r.lat
  lon.value = r.lon
  // el nombre se autorellena con el del sitio; se puede editar después
  name.value = r.display_name.split(',')[0].trim()
}

async function save() {
  if (!name.value.trim()) {
    toast.add({ severity: 'warn', summary: 'El nombre es obligatorio', life: 3000 })
    return
  }
  saving.value = true
  try {
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
    if (props.place) await store.update(props.place.id, payload)
    else await store.create(payload)
    visible.value = false
    emit('saved')
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error al guardar', detail: String(err), life: 5000 })
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <Dialog
    v-model:visible="visible"
    modal
    :header="place ? 'Editar sitio' : 'Nuevo sitio'"
    class="w-full max-w-lg mx-4"
  >
    <div class="flex flex-col gap-4">
      <div class="flex flex-col gap-1">
        <label class="text-sm font-medium">Ubicación</label>
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
        <p v-if="lat != null && lon != null" class="text-xs text-slate-400">
          <i class="pi pi-map-marker text-[10px]" /> {{ lat.toFixed(5) }}, {{ lon.toFixed(5) }}
        </p>
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">Nombre *</label>
          <InputText v-model="name" placeholder="Fushimi Inari" />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">Categoría</label>
          <Select
            v-model="category"
            :options="categoryOptions"
            optionLabel="label"
            optionValue="value"
          />
        </div>
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">Latitud</label>
          <InputNumber v-model="lat" :minFractionDigits="0" :maxFractionDigits="6" locale="en-US" />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">Longitud</label>
          <InputNumber v-model="lon" :minFractionDigits="0" :maxFractionDigits="6" locale="en-US" />
        </div>
      </div>

      <div class="flex flex-col gap-1">
        <label class="text-sm font-medium">Enlace</label>
        <InputText v-model="url" placeholder="https://…" />
      </div>
      <div class="flex flex-col gap-1">
        <label class="text-sm font-medium">Notas</label>
        <Textarea v-model="notes" rows="2" autoResize />
      </div>
      <div class="flex items-center gap-6">
        <label class="flex items-center gap-2 text-sm">
          <Checkbox v-model="mustSee" binary /> Imprescindible
          <i class="pi pi-star-fill text-amber-400 text-xs" />
        </label>
        <label class="flex items-center gap-2 text-sm">
          <Checkbox v-model="visited" binary /> Visitado
        </label>
      </div>
    </div>
    <template #footer>
      <Button label="Cancelar" severity="secondary" text @click="visible = false" />
      <Button :label="place ? 'Guardar' : 'Añadir sitio'" :loading="saving" @click="save" />
    </template>
  </Dialog>
</template>
