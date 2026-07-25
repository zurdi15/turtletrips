<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Textarea from 'primevue/textarea'
import Select from 'primevue/select'
import AutoComplete from 'primevue/autocomplete'
import Checkbox from 'primevue/checkbox'
import FormDialog from '../ui/FormDialog.vue'
import FormField from '../ui/FormField.vue'
import type { GeocodeResult, Place, PlaceCategory } from '../../api/types'
import { PLACE_CATEGORY_KEYS, toSelectOptions } from '../../constants'
import { usePlacesStore } from '../../stores/places'
import { useFormDialog } from '../../composables/useFormDialog'
import { useGeocodeSearch } from '../../composables/useGeocode'

const props = defineProps<{ place?: Place | null }>()
const visible = defineModel<boolean>('visible', { required: true })
const emit = defineEmits<{ saved: [] }>()

const { t } = useI18n()
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

const categoryOptions = computed(() => toSelectOptions(PLACE_CATEGORY_KEYS, t))

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
  validate: () => (name.value.trim() ? null : t('places.form.nameRequired')),
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
    :header="place ? t('places.form.editTitle') : t('places.form.newTitle')"
    :saving="saving"
    :saveLabel="place ? t('common.actions.save') : t('places.form.addLabel')"
    @save="save"
  >
    <FormField :label="t('places.form.location')">
      <AutoComplete
        v-model="geocodeQuery"
        :suggestions="results"
        optionLabel="display_name"
        :placeholder="t('places.form.locationPlaceholder')"
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
      <FormField :label="t('places.form.name')" required>
        <InputText v-model="name" :placeholder="t('places.form.namePlaceholder')" />
      </FormField>
      <FormField :label="t('places.form.category')">
        <Select
          v-model="category"
          :options="categoryOptions"
          optionLabel="label"
          optionValue="value"
        />
      </FormField>
    </div>

    <div class="grid grid-cols-2 gap-3">
      <FormField :label="t('places.form.lat')">
        <InputNumber v-model="lat" :minFractionDigits="0" :maxFractionDigits="6" locale="en-US" />
      </FormField>
      <FormField :label="t('places.form.lon')">
        <InputNumber v-model="lon" :minFractionDigits="0" :maxFractionDigits="6" locale="en-US" />
      </FormField>
    </div>

    <FormField :label="t('places.form.link')">
      <InputText v-model="url" placeholder="https://…" />
    </FormField>
    <FormField :label="t('places.form.notes')">
      <Textarea v-model="notes" rows="2" autoResize />
    </FormField>
    <div class="flex items-center gap-6">
      <label class="flex items-center gap-2 text-sm">
        <Checkbox v-model="mustSee" binary /> {{ t('places.mustSee') }}
        <i class="pi pi-star-fill text-amber-400 text-xs" />
      </label>
      <label class="flex items-center gap-2 text-sm">
        <Checkbox v-model="visited" binary /> {{ t('places.form.visited') }}
      </label>
    </div>
  </FormDialog>
</template>
