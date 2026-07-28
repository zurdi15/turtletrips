<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Select from 'primevue/select'
import MultiSelect from 'primevue/multiselect'
import InputNumber from 'primevue/inputnumber'
import Button from 'primevue/button'
import DateRangePicker from '../DateRangePicker.vue'
import MemberChip from '../MemberChip.vue'
import CountrySelect from '../ui/CountrySelect.vue'
import FormField from '../ui/FormField.vue'
import TravelerAvatar from '../ui/TravelerAvatar.vue'
import type { Traveler, Trip, TripStatus } from '../../api/types'
import { api } from '../../api/client'
import { CURRENCIES, TRIP_STATUS_KEYS, toSelectOptions } from '../../constants'
import { intlLocale } from '../../i18n'
import { countryName } from '../../countries'
import { useSessionStore } from '../../stores/session'
import { useTripsStore } from '../../stores/trips'
import { useTravelersStore } from '../../stores/travelers'
import { useNotify } from '../../composables/useNotify'
import { parseIsoDate, toIsoDate } from '../../composables/useMoney'

// Campos del viaje compartidos entre TripFormDialog (crear) y la tab Ajustes
// (editar inline). Se monta fresco en cada uso, así que el estado se
// inicializa directamente desde la entidad; el padre orquesta validate/submit.
const props = withDefaults(defineProps<{ trip?: Trip | null; autofocus?: boolean }>(), {
  trip: null,
  autofocus: false,
})

const { t } = useI18n()
const notify = useNotify()
const store = useTripsStore()
const travelersStore = useTravelersStore()
const session = useSessionStore()
travelersStore.load()

const name = ref(props.trip?.name ?? '')
const countries = ref<string[]>(props.trip?.countries ? [...props.trip.countries] : [])
// al crear, el propio viajero viene preseleccionado (el backend lo garantiza
// igualmente, pero así el formulario lo enseña desde el principio)
const travelerIds = ref<number[]>(
  props.trip?.travelers?.map((tr) => tr.id) ??
    (session.travelerId !== null ? [session.travelerId] : []),
)
const startDate = ref<Date | null>(props.trip?.start_date ? parseIsoDate(props.trip.start_date) : null)
const endDate = ref<Date | null>(props.trip?.end_date ? parseIsoDate(props.trip.end_date) : null)
const baseCurrency = ref(props.trip?.base_currency ?? 'EUR')
const budget = ref<number | null>(props.trip?.budget_amount ?? null)
const albumUrl = ref(props.trip?.album_url ?? '')
const notes = ref(props.trip?.notes ?? '')
// 'auto' como centinela: con null PrimeVue mostraba el placeholder vacío
const statusOverride = ref<TripStatus | 'auto'>(props.trip?.status_override ?? 'auto')
const uploadingCover = ref(false)
const coverInput = ref<HTMLInputElement>()

const statusOptions = computed(() => [
  { value: 'auto', label: t('trips.form.statusAuto') },
  ...toSelectOptions(TRIP_STATUS_KEYS, t),
])

const numberLocale = computed(() => intlLocale())

// --- buscador de fotos online para la portada (Wikimedia Commons) ---
interface ImageResult {
  title: string
  thumb_url: string
  image_url: string
}
const showPhotoSearch = ref(false)
const photoQuery = ref('')
const photoResults = ref<ImageResult[]>([])
const photoSearched = ref(false)
const searchingPhotos = ref(false)
const applyingPhoto = ref<string | null>(null)

function togglePhotoSearch() {
  showPhotoSearch.value = !showPhotoSearch.value
  if (showPhotoSearch.value && !photoQuery.value) {
    photoQuery.value = countries.value.length
      ? countryName(countries.value[0])
      : name.value
  }
}

async function searchPhotos() {
  const q = photoQuery.value.trim()
  if (q.length < 2) return
  searchingPhotos.value = true
  try {
    photoResults.value = await api.get<ImageResult[]>(
      `/image-search?q=${encodeURIComponent(q)}`,
    )
  } catch {
    photoResults.value = []
  } finally {
    photoSearched.value = true
    searchingPhotos.value = false
  }
}

async function applyPhoto(result: ImageResult) {
  if (!props.trip) return
  applyingPhoto.value = result.image_url
  try {
    await store.setCoverFromUrl(props.trip.id, result.image_url)
    notify.success(t('trips.toast.coverUpdated'))
    showPhotoSearch.value = false
  } catch (err) {
    notify.error(t('trips.toast.coverSaveError'), err)
  } finally {
    applyingPhoto.value = null
  }
}

function travelerById(id: number): Traveler | undefined {
  return travelersStore.items.find((t) => t.id === id)
}

async function onCoverChosen(event: Event) {
  if (!props.trip) return
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  uploadingCover.value = true
  try {
    await store.uploadCover(props.trip.id, file)
    notify.success(t('trips.toast.coverUpdated'))
  } catch (err) {
    notify.error(t('trips.toast.coverUploadError'), err)
  } finally {
    uploadingCover.value = false
    target.value = ''
  }
}

async function removeCover() {
  if (!props.trip) return
  await store.deleteCover(props.trip.id)
}

function validate(): string | null {
  return name.value.trim() ? null : t('trips.form.nameRequired')
}

async function submit(): Promise<Trip> {
  const payload = {
    name: name.value.trim(),
    countries: countries.value,
    start_date: startDate.value ? toIsoDate(startDate.value) : null,
    end_date: endDate.value ? toIsoDate(endDate.value) : null,
    base_currency: baseCurrency.value,
    budget_amount: budget.value,
    album_url: albumUrl.value.trim() || null,
    notes: notes.value || null,
    status_override: statusOverride.value === 'auto' ? null : statusOverride.value,
    traveler_ids: travelerIds.value,
  }
  return props.trip
    ? await store.updateTrip(props.trip.id, payload)
    : await store.createTrip(payload)
}

defineExpose({ validate, submit })
</script>

<template>
  <div class="flex flex-col gap-4">
    <FormField :label="t('trips.form.name')" required>
      <InputText v-model="name" :placeholder="t('trips.form.namePlaceholder')" :autofocus="autofocus" />
    </FormField>
    <FormField :label="t('trips.form.countries')">
      <CountrySelect
        v-model="countries"
        multiple
        :placeholder="t('trips.form.countriesPlaceholder')"
      />
    </FormField>
    <FormField :label="t('trips.form.travelers')">
      <MultiSelect
        v-model="travelerIds"
        :options="travelersStore.items"
        optionLabel="name"
        optionValue="id"
        filter
        display="chip"
        :placeholder="t('trips.form.travelersPlaceholder')"
        :maxSelectedLabels="8"
      >
        <template #option="{ option }">
          <span class="flex items-center gap-2">
            <span class="w-4 h-4 grid place-items-center overflow-hidden shrink-0">
              <TravelerAvatar
                :name="option.name"
                :color="option.color"
                :avatar-url="option.avatar_url"
                size="xs"
              />
            </span>
            {{ option.name }}
          </span>
        </template>
        <!-- chips seleccionados con el dot de color de cada viajero -->
        <template #chip="{ value, removeCallback }">
          <MemberChip
            v-if="travelerById(value)"
            :member="travelerById(value)!"
            removable
            @remove="(e) => removeCallback(e, value)"
          />
        </template>
      </MultiSelect>
      <template #hint>
        <span class="text-xs text-ink-faint">
          {{ t('trips.form.travelersHint') }}
        </span>
      </template>
    </FormField>
    <FormField :label="t('trips.form.dates')">
      <DateRangePicker v-model:start="startDate" v-model:end="endDate" clearable />
    </FormField>
    <div class="grid grid-cols-2 gap-3">
      <FormField :label="t('trips.form.baseCurrency')">
        <Select v-model="baseCurrency" :options="CURRENCIES" filter />
      </FormField>
      <FormField :label="t('trips.form.budget')">
        <InputNumber
          v-model="budget"
          mode="currency"
          :currency="baseCurrency"
          :locale="numberLocale"
          :min="0"
          :placeholder="t('trips.form.budgetPlaceholder')"
        />
      </FormField>
    </div>
    <FormField :label="t('trips.form.status')">
      <Select
        v-model="statusOverride"
        :options="statusOptions"
        optionLabel="label"
        optionValue="value"
      />
    </FormField>
    <div v-if="trip" class="flex flex-col gap-1">
      <label class="text-sm font-medium">{{ t('trips.form.cover') }}</label>
      <div class="flex items-center gap-2">
        <input ref="coverInput" type="file" accept="image/*" class="hidden" @change="onCoverChosen" />
        <Button
          :label="trip.cover_url ? t('trips.form.changePhoto') : t('trips.form.uploadPhoto')"
          icon="pi pi-image"
          severity="secondary"
          outlined
          size="small"
          :loading="uploadingCover"
          @click="coverInput?.click()"
        />
        <Button
          :label="t('trips.form.searchOnline')"
          icon="pi pi-search"
          severity="secondary"
          outlined
          size="small"
          @click="togglePhotoSearch"
        />
        <Button
          v-if="trip.cover_url"
          :label="t('trips.form.removePhoto')"
          severity="danger"
          text
          size="small"
          @click="removeCover"
        />
      </div>
      <span v-if="!trip.cover_url" class="text-xs text-ink-faint">
        {{ t('trips.form.noCoverHint') }}
      </span>

      <!-- buscador de fotos (Wikimedia Commons): clic en una para usarla -->
      <div v-if="showPhotoSearch" class="flex flex-col gap-2 mt-1">
        <div class="flex gap-2">
          <InputText
            v-model="photoQuery"
            :placeholder="t('trips.form.photoSearchPlaceholder')"
            class="flex-1"
            @keyup.enter="searchPhotos"
          />
          <Button icon="pi pi-search" :loading="searchingPhotos" @click="searchPhotos" />
        </div>
        <div v-if="photoResults.length" class="grid grid-cols-3 gap-2 max-h-60 overflow-y-auto">
          <button
            v-for="r in photoResults"
            :key="r.image_url"
            type="button"
            class="relative aspect-video rounded-lg overflow-hidden border border-line hover:ring-2 hover:ring-primary cursor-pointer"
            :title="r.title"
            @click="applyPhoto(r)"
          >
            <img :src="r.thumb_url" class="w-full h-full object-cover" loading="lazy" alt="" />
            <span
              v-if="applyingPhoto === r.image_url"
              class="absolute inset-0 bg-black/40 flex items-center justify-center text-white"
            >
              <i class="pi pi-spinner pi-spin" />
            </span>
          </button>
        </div>
        <p v-else-if="photoSearched && !searchingPhotos" class="text-xs text-ink-faint">
          {{ t('trips.form.photoNoResults') }}
        </p>
        <p class="text-xs text-ink-faint">{{ t('trips.form.photoCredit') }}</p>
      </div>
    </div>
    <FormField :label="t('trips.form.album')">
      <InputText v-model="albumUrl" type="url" placeholder="https://photos.app.goo.gl/…" />
      <template #hint>
        <span class="text-xs text-ink-faint">
          {{ t('trips.form.albumHint') }}
        </span>
      </template>
    </FormField>
    <FormField :label="t('trips.form.notes')">
      <Textarea v-model="notes" rows="3" autoResize />
    </FormField>
  </div>
</template>
