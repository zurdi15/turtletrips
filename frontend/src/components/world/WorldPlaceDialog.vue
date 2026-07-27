<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import Textarea from 'primevue/textarea'
import FormDialog from '../ui/FormDialog.vue'
import FormField from '../ui/FormField.vue'
import UploadButton from '../ui/UploadButton.vue'
import type { WorldPlace, WorldPlaceKind } from '../../api/types'
import { countryOptions } from '../../countries'
import { intlLocale } from '../../i18n'
import { displayName } from '../../utils/worldGrouping'
import { useWorldPlacesStore } from '../../stores/worldPlaces'
import { useFormDialog } from '../../composables/useFormDialog'
import { useNotify } from '../../composables/useNotify'

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
const notify = useNotify()

const formName = ref('')
const formKind = ref<WorldPlaceKind>('city')
const formNote = ref('')
const formLat = ref<number | null>(null)
const formLon = ref<number | null>(null)
const formCountry = ref<string | null>(null)
// cuándo se visitó (opcional, retroactivo): alimenta las estadísticas anuales
const formYear = ref<number | null>(null)
const formMonth = ref<number | null>(null)

const kindOptions = computed(() => [
  { value: 'city', label: t('world.kind.city') },
  { value: 'place', label: t('world.kind.place') },
  { value: 'country', label: t('world.kind.country') },
])

const dialogCountryOptions = computed(() => [
  { code: null as string | null, label: t('world.noCountry') },
  ...countryOptions().map((o) => ({ code: o.code as string | null, label: o.label })),
])

// ---- postal (solo países ya guardados; se sube al momento) ----

const photoUrl = ref<string | null>(null)
const uploadingPhoto = ref(false)

async function onPhotoChosen(file: File) {
  if (!props.place) return
  uploadingPhoto.value = true
  try {
    const updated = await store.uploadPhoto(props.place.id, file)
    photoUrl.value = updated.photo_url
  } catch (err) {
    notify.error(t('world.toast.photoError'), err)
  } finally {
    uploadingPhoto.value = false
  }
}

async function removePhoto() {
  if (!props.place) return
  await store.removePhoto(props.place.id)
  photoUrl.value = null
}

const CURRENT_YEAR = new Date().getFullYear()
const yearOptions = computed(() => [
  { value: null as number | null, label: t('world.form.noYear') },
  ...Array.from({ length: CURRENT_YEAR - 1949 }, (_, i) => {
    const year = CURRENT_YEAR - i
    return { value: year as number | null, label: String(year) }
  }),
])

const monthOptions = computed(() => [
  { value: null as number | null, label: '—' },
  ...Array.from({ length: 12 }, (_, i) => ({
    value: (i + 1) as number | null,
    label: new Date(2000, i, 1).toLocaleDateString(intlLocale(), { month: 'long' }),
  })),
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
      formYear.value = place.visited_year
      formMonth.value = place.visited_month
      photoUrl.value = place.photo_url
    } else {
      formName.value = props.prefill?.name ?? ''
      formKind.value = props.prefill?.kind ?? 'city'
      formNote.value = ''
      formLat.value = props.prefill?.lat ?? null
      formLon.value = props.prefill?.lon ?? null
      formCountry.value = props.prefill?.country_code ?? null
      formYear.value = null
      formMonth.value = null
      photoUrl.value = null
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
      visited_year: formYear.value,
      // el mes sin año no significa nada
      visited_month: formYear.value != null ? formMonth.value : null,
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
    <!-- cuándo se visitó (retroactivo): da sentido a las estadísticas anuales -->
    <div class="grid grid-cols-2 gap-3">
      <FormField :label="t('world.form.visitedYear')">
        <Select
          v-model="formYear"
          :options="yearOptions"
          optionLabel="label"
          optionValue="value"
          filter
        />
      </FormField>
      <FormField :label="t('world.form.visitedMonth')">
        <Select
          v-model="formMonth"
          :options="monthOptions"
          optionLabel="label"
          optionValue="value"
          :disabled="formYear == null"
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
    <!-- postal del país: una foto que lo resuma (solo al editar) -->
    <div v-if="place && place.kind === 'country'" class="flex flex-col gap-2">
      <label class="text-sm font-medium">{{ t('world.form.photo') }}</label>
      <img
        v-if="photoUrl"
        :src="photoUrl"
        class="w-full max-h-40 object-cover rounded-lg border border-line"
        alt=""
      />
      <div class="flex items-center gap-2">
        <UploadButton
          :label="photoUrl ? t('world.form.changePhoto') : t('world.form.uploadPhoto')"
          icon="pi pi-image"
          severity="secondary"
          outlined
          size="small"
          accept="image/*"
          :loading="uploadingPhoto"
          @file="onPhotoChosen"
        />
        <Button
          v-if="photoUrl"
          :label="t('world.form.removePhoto')"
          severity="danger"
          text
          size="small"
          @click="removePhoto"
        />
      </div>
    </div>
    <p v-if="place?.auto" class="text-xs text-ink-faint">
      <i class="pi pi-info-circle" /> {{ t('world.form.autoInfo', { origin: place.origin }) }}
    </p>
  </FormDialog>
</template>
