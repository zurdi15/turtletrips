<script setup lang="ts">
import { ref, watch } from 'vue'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Select from 'primevue/select'
import MultiSelect from 'primevue/multiselect'
import InputNumber from 'primevue/inputnumber'
import Button from 'primevue/button'
import DateRangePicker from './DateRangePicker.vue'
import { useToast } from 'primevue/usetoast'
import type { Trip, TripStatus } from '../api/types'
import { api } from '../api/client'
import { CURRENCIES, TRIP_STATUS_LABELS, toSelectOptions } from '../constants'
import { COUNTRY_OPTIONS, countryName } from '../countries'
import { useTripsStore } from '../stores/trips'
import { parseIsoDate, toIsoDate } from '../composables/useMoney'

const props = defineProps<{ trip?: Trip | null }>()
const visible = defineModel<boolean>('visible', { required: true })
const emit = defineEmits<{ saved: [trip: Trip] }>()

const toast = useToast()
const store = useTripsStore()

const name = ref('')
const countries = ref<string[]>([])
const startDate = ref<Date | null>(null)
const endDate = ref<Date | null>(null)
const baseCurrency = ref('EUR')
const budget = ref<number | null>(null)
const albumUrl = ref('')
const notes = ref('')
// 'auto' como centinela: con null PrimeVue mostraba el placeholder vacío
const statusOverride = ref<TripStatus | 'auto'>('auto')
const saving = ref(false)
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
    toast.add({ severity: 'success', summary: 'Portada actualizada', life: 3000 })
    showPhotoSearch.value = false
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error al guardar la portada', detail: String(err), life: 5000 })
  } finally {
    applyingPhoto.value = null
  }
}

watch(visible, (open) => {
  if (!open) return
  const t = props.trip
  name.value = t?.name ?? ''
  countries.value = t?.countries ? [...t.countries] : []
  startDate.value = t?.start_date ? parseIsoDate(t.start_date) : null
  endDate.value = t?.end_date ? parseIsoDate(t.end_date) : null
  baseCurrency.value = t?.base_currency ?? 'EUR'
  budget.value = t?.budget_amount ?? null
  albumUrl.value = t?.album_url ?? ''
  notes.value = t?.notes ?? ''
  statusOverride.value = t?.status_override ?? 'auto'
  showPhotoSearch.value = false
  photoQuery.value = ''
  photoResults.value = []
  photoSearched.value = false
})

async function onCoverChosen(event: Event) {
  if (!props.trip) return
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  uploadingCover.value = true
  try {
    await store.uploadCover(props.trip.id, file)
    toast.add({ severity: 'success', summary: 'Portada actualizada', life: 3000 })
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error al subir la portada', detail: String(err), life: 5000 })
  } finally {
    uploadingCover.value = false
    target.value = ''
  }
}

async function removeCover() {
  if (!props.trip) return
  await store.deleteCover(props.trip.id)
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
      countries: countries.value,
      start_date: startDate.value ? toIsoDate(startDate.value) : null,
      end_date: endDate.value ? toIsoDate(endDate.value) : null,
      base_currency: baseCurrency.value,
      budget_amount: budget.value,
      album_url: albumUrl.value.trim() || null,
      notes: notes.value || null,
      status_override: statusOverride.value === 'auto' ? null : statusOverride.value,
    }
    const trip = props.trip
      ? await store.updateTrip(props.trip.id, payload)
      : await store.createTrip(payload)
    visible.value = false
    emit('saved', trip)
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
    :header="trip ? 'Editar viaje' : 'Nuevo viaje'"
    class="w-full max-w-lg mx-4"
  >
    <div class="flex flex-col gap-4">
      <div class="flex flex-col gap-1">
        <label class="text-sm font-medium">Nombre *</label>
        <InputText v-model="name" placeholder="Japón 2026" autofocus />
      </div>
      <div class="flex flex-col gap-1">
        <label class="text-sm font-medium">Países</label>
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
      </div>
      <div class="flex flex-col gap-1">
        <label class="text-sm font-medium">Fechas</label>
        <DateRangePicker v-model:start="startDate" v-model:end="endDate" clearable />
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">Moneda base</label>
          <Select v-model="baseCurrency" :options="CURRENCIES" filter />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">Presupuesto</label>
          <InputNumber
            v-model="budget"
            mode="currency"
            :currency="baseCurrency"
            locale="es-ES"
            :min="0"
            placeholder="Opcional"
          />
        </div>
      </div>
      <div class="flex flex-col gap-1">
        <label class="text-sm font-medium">Estado</label>
        <Select
          v-model="statusOverride"
          :options="statusOptions"
          optionLabel="label"
          optionValue="value"
        />
      </div>
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
        <span v-if="!trip.cover_url" class="text-xs text-slate-400">
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
              class="relative aspect-video rounded-lg overflow-hidden border border-slate-200 hover:ring-2 hover:ring-[var(--p-primary-color)] cursor-pointer"
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
          <p v-else-if="photoSearched && !searchingPhotos" class="text-xs text-slate-400">
            Sin resultados: prueba con el nombre del país o la ciudad en inglés
          </p>
          <p class="text-xs text-slate-400">Fotos de Wikimedia Commons</p>
        </div>
      </div>
      <div class="flex flex-col gap-1">
        <label class="text-sm font-medium">Álbum de fotos</label>
        <InputText v-model="albumUrl" type="url" placeholder="https://photos.app.goo.gl/…" />
        <span class="text-xs text-slate-400">Enlace externo (Google Photos, etc.), accesible desde la cabecera del viaje</span>
      </div>
      <div class="flex flex-col gap-1">
        <label class="text-sm font-medium">Notas</label>
        <Textarea v-model="notes" rows="3" autoResize />
      </div>
    </div>
    <template #footer>
      <Button label="Cancelar" severity="secondary" text @click="visible = false" />
      <Button :label="trip ? 'Guardar' : 'Crear viaje'" :loading="saving" @click="save" />
    </template>
  </Dialog>
</template>
