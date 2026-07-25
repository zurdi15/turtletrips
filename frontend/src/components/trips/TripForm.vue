<script setup lang="ts">
import { ref } from 'vue'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Select from 'primevue/select'
import MultiSelect from 'primevue/multiselect'
import InputNumber from 'primevue/inputnumber'
import Button from 'primevue/button'
import DateRangePicker from '../DateRangePicker.vue'
import MemberChip from '../MemberChip.vue'
import FormField from '../ui/FormField.vue'
import type { Traveler, Trip, TripStatus } from '../../api/types'
import { api } from '../../api/client'
import { CURRENCIES, TRIP_STATUS_LABELS, toSelectOptions } from '../../constants'
import { MEMBER_COLORS } from '../../theme'
import { FALLBACK_CATEGORY_COLOR } from '../../stores/categories'
import { COUNTRY_OPTIONS, countryName } from '../../countries'
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

const notify = useNotify()
const store = useTripsStore()
const travelersStore = useTravelersStore()
travelersStore.load()

const name = ref(props.trip?.name ?? '')
const countries = ref<string[]>(props.trip?.countries ? [...props.trip.countries] : [])
const travelerIds = ref<number[]>(props.trip?.travelers?.map((tr) => tr.id) ?? [])
const newTravelerName = ref('')
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

const statusOptions = [
  { value: 'auto', label: 'Automático (según fechas)' },
  ...toSelectOptions(TRIP_STATUS_LABELS),
]

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
    notify.success('Portada actualizada')
    showPhotoSearch.value = false
  } catch (err) {
    notify.error('Error al guardar la portada', err)
  } finally {
    applyingPhoto.value = null
  }
}

function travelerById(id: number): Traveler | undefined {
  return travelersStore.items.find((t) => t.id === id)
}

async function addNewTraveler() {
  const nm = newTravelerName.value.trim()
  if (!nm) return
  try {
    const color = MEMBER_COLORS[travelersStore.items.length % MEMBER_COLORS.length]
    const traveler = await travelersStore.create(nm, color)
    if (!travelerIds.value.includes(traveler.id)) travelerIds.value.push(traveler.id)
    newTravelerName.value = ''
  } catch (err) {
    notify.error('Error al añadir', err)
  }
}

async function onCoverChosen(event: Event) {
  if (!props.trip) return
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  uploadingCover.value = true
  try {
    await store.uploadCover(props.trip.id, file)
    notify.success('Portada actualizada')
  } catch (err) {
    notify.error('Error al subir la portada', err)
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
  return name.value.trim() ? null : 'El nombre es obligatorio'
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
    <FormField label="Nombre" required>
      <InputText v-model="name" placeholder="Japón 2026" :autofocus="autofocus" />
    </FormField>
    <FormField label="Países">
      <MultiSelect
        v-model="countries"
        :options="COUNTRY_OPTIONS"
        optionLabel="label"
        optionValue="code"
        filter
        placeholder="Busca países…"
        display="chip"
        :maxSelectedLabels="6"
        :virtualScrollerOptions="{ itemSize: 38 }"
      />
    </FormField>
    <FormField label="Viajeros">
      <MultiSelect
        v-model="travelerIds"
        :options="travelersStore.items"
        optionLabel="name"
        optionValue="id"
        filter
        display="chip"
        placeholder="Selecciona viajeros…"
        :maxSelectedLabels="8"
      >
        <template #option="{ option }">
          <span class="flex items-center gap-2">
            <span
              class="w-3 h-3 rounded-full shrink-0"
              :style="{ background: option.color ?? FALLBACK_CATEGORY_COLOR }"
            />
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
      <div class="flex gap-2">
        <InputText
          v-model="newTravelerName"
          placeholder="Crear un viajero nuevo…"
          class="flex-1 min-w-0"
          @keyup.enter="addNewTraveler"
        />
        <Button
          label="Añadir"
          icon="pi pi-plus"
          severity="secondary"
          outlined
          class="shrink-0 max-sm:[&_.p-button-label]:hidden"
          @click="addNewTraveler"
        />
      </div>
      <template #hint>
        <span class="text-xs text-ink-faint">
          Globales y reutilizables: marca quién viaja para poder repartir gastos
        </span>
      </template>
    </FormField>
    <FormField label="Fechas">
      <DateRangePicker v-model:start="startDate" v-model:end="endDate" clearable />
    </FormField>
    <div class="grid grid-cols-2 gap-3">
      <FormField label="Moneda base">
        <Select v-model="baseCurrency" :options="CURRENCIES" filter />
      </FormField>
      <FormField label="Presupuesto">
        <InputNumber
          v-model="budget"
          mode="currency"
          :currency="baseCurrency"
          locale="es-ES"
          :min="0"
          placeholder="Opcional"
        />
      </FormField>
    </div>
    <FormField label="Estado">
      <Select
        v-model="statusOverride"
        :options="statusOptions"
        optionLabel="label"
        optionValue="value"
      />
    </FormField>
    <div v-if="trip" class="flex flex-col gap-1">
      <label class="text-sm font-medium">Foto de portada</label>
      <div class="flex items-center gap-2">
        <input ref="coverInput" type="file" accept="image/*" class="hidden" @change="onCoverChosen" />
        <Button
          :label="trip.cover_url ? 'Cambiar foto' : 'Subir foto'"
          icon="pi pi-image"
          severity="secondary"
          outlined
          size="small"
          :loading="uploadingCover"
          @click="coverInput?.click()"
        />
        <Button
          label="Buscar online"
          icon="pi pi-search"
          severity="secondary"
          outlined
          size="small"
          @click="togglePhotoSearch"
        />
        <Button
          v-if="trip.cover_url"
          label="Quitar"
          severity="danger"
          text
          size="small"
          @click="removeCover"
        />
      </div>
      <span v-if="!trip.cover_url" class="text-xs text-ink-faint">
        Sin foto se usa una imagen del país automáticamente
      </span>

      <!-- buscador de fotos (Wikimedia Commons): clic en una para usarla -->
      <div v-if="showPhotoSearch" class="flex flex-col gap-2 mt-1">
        <div class="flex gap-2">
          <InputText
            v-model="photoQuery"
            placeholder="Taiwán, Alishan, Jiufen…"
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
          Sin resultados: prueba con el nombre del país o la ciudad en inglés
        </p>
        <p class="text-xs text-ink-faint">Fotos de Wikimedia Commons</p>
      </div>
    </div>
    <FormField label="Álbum de fotos">
      <InputText v-model="albumUrl" type="url" placeholder="https://photos.app.goo.gl/…" />
      <template #hint>
        <span class="text-xs text-ink-faint">
          Enlace externo (Google Photos, etc.), accesible desde la cabecera del viaje
        </span>
      </template>
    </FormField>
    <FormField label="Notas">
      <Textarea v-model="notes" rows="3" autoResize />
    </FormField>
  </div>
</template>
