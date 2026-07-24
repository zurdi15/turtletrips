<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import DatePicker from 'primevue/datepicker'
import Select from 'primevue/select'
import Button from 'primevue/button'
import DateRangePicker from './DateRangePicker.vue'
import { useToast } from 'primevue/usetoast'
import type { ItineraryItem } from '../api/types'
import { useItineraryStore } from '../stores/itinerary'
import { usePlacesStore } from '../stores/places'
import { useBookingsStore } from '../stores/bookings'
import { parseIsoDate, toIsoDate } from '../composables/useMoney'

const props = defineProps<{ item?: ItineraryItem | null; presetDay?: string | null }>()
const visible = defineModel<boolean>('visible', { required: true })
const emit = defineEmits<{ saved: [] }>()

const toast = useToast()
const store = useItineraryStore()
const places = usePlacesStore()
const bookings = useBookingsStore()

const day = ref<Date | null>(new Date())
const endDay = ref<Date | null>(null)
const title = ref('')
const startTime = ref<Date | null>(null)
const endTime = ref<Date | null>(null)
const notes = ref('')
const placeId = ref<number | null>(null)
const bookingId = ref<number | null>(null)
const saving = ref(false)

const placeOptions = computed(() => [
  { value: null, label: 'Ninguno' },
  ...places.items.map((p) => ({ value: p.id, label: p.name })),
])
const bookingOptions = computed(() => [
  { value: null, label: 'Ninguna' },
  ...bookings.items.map((b) => ({ value: b.id, label: b.title })),
])

watch(visible, (open) => {
  if (!open) return
  const i = props.item
  day.value = i ? parseIsoDate(i.day) : props.presetDay ? parseIsoDate(props.presetDay) : new Date()
  endDay.value = i?.end_day ? parseIsoDate(i.end_day) : null
  title.value = i?.title ?? ''
  startTime.value = i?.start_time ? new Date(`1970-01-01T${i.start_time}`) : null
  endTime.value = i?.end_time ? new Date(`1970-01-01T${i.end_time}`) : null
  notes.value = i?.notes ?? ''
  placeId.value = i?.place_id ?? null
  bookingId.value = i?.booking_id ?? null
})

// autocompletar el título al enlazar un sitio o reserva
watch(placeId, (id) => {
  if (id != null && !title.value.trim()) {
    title.value = places.items.find((p) => p.id === id)?.name ?? ''
  }
})
watch(bookingId, (id) => {
  if (id != null && !title.value.trim()) {
    title.value = bookings.items.find((b) => b.id === id)?.title ?? ''
  }
})

function toTime(d: Date | null): string | null {
  if (!d) return null
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}:00`
}

async function save() {
  if (!title.value.trim()) {
    toast.add({ severity: 'warn', summary: 'El título es obligatorio', life: 3000 })
    return
  }
  if (!day.value) {
    toast.add({ severity: 'warn', summary: 'El día es obligatorio', life: 3000 })
    return
  }
  saving.value = true
  try {
    const payload = {
      day: toIsoDate(day.value),
      end_day: endDay.value && endDay.value > day.value ? toIsoDate(endDay.value) : null,
      title: title.value.trim(),
      start_time: toTime(startTime.value),
      end_time: toTime(endTime.value),
      notes: notes.value || null,
      place_id: placeId.value,
      booking_id: bookingId.value,
    }
    if (props.item) await store.update(props.item.id, payload)
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
    :header="item ? 'Editar actividad' : 'Nueva actividad'"
    class="w-full max-w-lg mx-4"
  >
    <div class="flex flex-col gap-4">
      <div class="flex flex-col gap-1">
        <label class="text-sm font-medium">Título *</label>
        <InputText v-model="title" placeholder="Visitar Fushimi Inari" autofocus />
      </div>
      <div class="flex flex-col gap-1">
        <label class="text-sm font-medium">Día(s) *</label>
        <DateRangePicker v-model:start="day" v-model:end="endDay" startLabel="Desde" endLabel="Hasta" />
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">Hora inicio</label>
          <DatePicker v-model="startTime" timeOnly hourFormat="24" />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">Hora fin</label>
          <DatePicker v-model="endTime" timeOnly hourFormat="24" />
        </div>
      </div>
      <p class="text-xs text-slate-400 -mt-2">
        Deja "Hasta" vacío para actividades de un solo día; rellénalo para estancias (p. ej. una ciudad del 3 al 6).
      </p>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">Sitio enlazado</label>
          <Select
            v-model="placeId"
            :options="placeOptions"
            optionLabel="label"
            optionValue="value"
            filter
          />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">Reserva enlazada</label>
          <Select
            v-model="bookingId"
            :options="bookingOptions"
            optionLabel="label"
            optionValue="value"
            filter
          />
        </div>
      </div>
      <div class="flex flex-col gap-1">
        <label class="text-sm font-medium">Notas</label>
        <Textarea v-model="notes" rows="2" autoResize />
      </div>
    </div>
    <template #footer>
      <Button label="Cancelar" severity="secondary" text @click="visible = false" />
      <Button :label="item ? 'Guardar' : 'Añadir'" :loading="saving" @click="save" />
    </template>
  </Dialog>
</template>
