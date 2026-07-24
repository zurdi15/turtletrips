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
import type { Trip } from '../api/types'
import { CURRENCIES, TRIP_STATUS_LABELS, toSelectOptions } from '../constants'
import { COUNTRY_OPTIONS } from '../countries'
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
const statusOverride = ref<string | null>(null)
const saving = ref(false)
const uploadingCover = ref(false)
const coverInput = ref<HTMLInputElement>()

const statusOptions = [
  { value: null, label: 'Automático (según fechas)' },
  ...toSelectOptions(TRIP_STATUS_LABELS),
]

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
  statusOverride.value = t?.status_override ?? null
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
      status_override: statusOverride.value,
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
      <div v-if="trip" class="flex flex-col gap-1">
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
            v-if="trip.cover_url"
            label="Quitar"
            severity="danger"
            text
            size="small"
            @click="removeCover"
          />
          <span v-if="!trip.cover_url" class="text-xs text-slate-400">
            Sin foto se usa una imagen del país automáticamente
          </span>
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
