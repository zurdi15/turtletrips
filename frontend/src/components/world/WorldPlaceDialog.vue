<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import Textarea from 'primevue/textarea'
import FormDialog from '../ui/FormDialog.vue'
import FormField from '../ui/FormField.vue'
import type { WorldPlace, WorldPlaceKind } from '../../api/types'
import { countryOptions } from '../../countries'
import { displayName } from '../../utils/worldGrouping'
import { useWorldPlacesStore } from '../../stores/worldPlaces'
import { useFormDialog } from '../../composables/useFormDialog'

export interface WorldPlacePrefill {
  name: string
  kind: WorldPlaceKind
  lat: number | null
  lon: number | null
  country_code: string | null
}

const props = defineProps<{
  /** lugar a editar; null = alta */
  place: WorldPlace | null
  /** valores iniciales para el alta (p. ej. desde geocoding) */
  prefill?: WorldPlacePrefill | null
}>()

const emit = defineEmits<{ saved: [created: boolean] }>()

const visible = defineModel<boolean>('visible', { required: true })

const { t } = useI18n()
const store = useWorldPlacesStore()

const formName = ref('')
const formKind = ref<WorldPlaceKind>('city')
const formNote = ref('')
const formLat = ref<number | null>(null)
const formLon = ref<number | null>(null)
const formCountry = ref<string | null>(null)

const kindOptions = computed(() => [
  { value: 'city', label: t('world.kind.city') },
  { value: 'place', label: t('world.kind.place') },
  { value: 'country', label: t('world.kind.country') },
])

const dialogCountryOptions = computed(() => [
  { code: null as string | null, label: t('world.noCountry') },
  ...countryOptions().map((o) => ({ code: o.code as string | null, label: o.label })),
])

const { saving, save } = useFormDialog({
  visible,
  entity: () => props.place,
  reset(place) {
    if (place) {
      formName.value = displayName(place)
      formKind.value = place.kind
      formNote.value = place.note ?? ''
      formLat.value = place.lat
      formLon.value = place.lon
      formCountry.value = place.country_code
    } else {
      formName.value = props.prefill?.name ?? ''
      formKind.value = props.prefill?.kind ?? 'city'
      formNote.value = ''
      formLat.value = props.prefill?.lat ?? null
      formLon.value = props.prefill?.lon ?? null
      formCountry.value = props.prefill?.country_code ?? null
    }
  },
  validate: () => (formName.value.trim() ? null : t('world.form.nameRequired')),
  submit() {
    const payload = {
      name: formName.value.trim(),
      kind: formKind.value,
      note: formNote.value.trim() || null,
      lat: formLat.value,
      lon: formLon.value,
      country_code:
        formKind.value === 'country'
          ? (formCountry.value ?? props.place?.country_code)
          : formCountry.value,
    }
    return props.place ? store.update(props.place.id, payload) : store.create(payload)
  },
  onSaved: () => emit('saved', !props.place),
})
</script>

<template>
  <FormDialog
    v-model:visible="visible"
    :header="place ? t('world.form.editTitle') : t('world.form.addTitle')"
    width="md"
    :saving="saving"
    :saveLabel="place ? t('common.actions.save') : t('common.actions.add')"
    @save="save"
  >
    <FormField :label="t('world.form.name')" required>
      <InputText v-model="formName" autofocus />
    </FormField>
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
      <FormField :label="t('world.form.kind')">
        <Select v-model="formKind" :options="kindOptions" optionLabel="label" optionValue="value" />
      </FormField>
      <FormField v-if="formKind !== 'country'" :label="t('world.form.country')">
        <Select
          v-model="formCountry"
          :options="dialogCountryOptions"
          optionLabel="label"
          optionValue="code"
          filter
        />
      </FormField>
    </div>
    <FormField :label="t('world.form.note')">
      <Textarea
        v-model="formNote"
        rows="3"
        autoResize
        :placeholder="t('world.form.notePlaceholder')"
      />
    </FormField>
    <p v-if="place?.auto" class="text-xs text-ink-faint">
      <i class="pi pi-info-circle" /> {{ t('world.form.autoInfo', { origin: place.origin }) }}
    </p>
  </FormDialog>
</template>
