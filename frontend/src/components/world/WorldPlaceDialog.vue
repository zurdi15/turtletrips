<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import Textarea from 'primevue/textarea'
import { useToast } from 'primevue/usetoast'
import type { WorldPlace, WorldPlaceKind } from '../../api/types'
import { COUNTRY_OPTIONS } from '../../countries'
import { displayName } from '../../utils/worldGrouping'
import { useWorldPlacesStore } from '../../stores/worldPlaces'

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

const store = useWorldPlacesStore()
const toast = useToast()

const formName = ref('')
const formKind = ref<WorldPlaceKind>('city')
const formNote = ref('')
const formLat = ref<number | null>(null)
const formLon = ref<number | null>(null)
const formCountry = ref<string | null>(null)

const kindOptions = [
  { value: 'city', label: 'Ciudad' },
  { value: 'place', label: 'Sitio' },
  { value: 'country', label: 'País' },
]

const dialogCountryOptions = computed(() => [
  { code: null as string | null, label: 'Sin país asignado' },
  ...COUNTRY_OPTIONS.map((o) => ({ code: o.code as string | null, label: o.label })),
])

watch(visible, (open) => {
  if (!open) return
  if (props.place) {
    formName.value = displayName(props.place)
    formKind.value = props.place.kind
    formNote.value = props.place.note ?? ''
    formLat.value = props.place.lat
    formLon.value = props.place.lon
    formCountry.value = props.place.country_code
  } else {
    formName.value = props.prefill?.name ?? ''
    formKind.value = props.prefill?.kind ?? 'city'
    formNote.value = ''
    formLat.value = props.prefill?.lat ?? null
    formLon.value = props.prefill?.lon ?? null
    formCountry.value = props.prefill?.country_code ?? null
  }
})

async function save() {
  if (!formName.value.trim()) return
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
  try {
    if (props.place) await store.update(props.place.id, payload)
    else await store.create(payload)
    visible.value = false
    emit('saved', !props.place)
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error al guardar', detail: String(err), life: 4000 })
  }
}
</script>

<template>
  <Dialog
    v-model:visible="visible"
    modal
    :header="place ? 'Editar lugar' : 'Añadir al mapa'"
    class="w-full max-w-md mx-4"
  >
    <div class="flex flex-col gap-4">
      <div class="flex flex-col gap-1">
        <label class="text-sm font-medium">Nombre *</label>
        <InputText v-model="formName" autofocus />
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">Tipo</label>
          <Select
            v-model="formKind"
            :options="kindOptions"
            optionLabel="label"
            optionValue="value"
          />
        </div>
        <div v-if="formKind !== 'country'" class="flex flex-col gap-1">
          <label class="text-sm font-medium">País</label>
          <Select
            v-model="formCountry"
            :options="dialogCountryOptions"
            optionLabel="label"
            optionValue="code"
            filter
          />
        </div>
      </div>
      <div class="flex flex-col gap-1">
        <label class="text-sm font-medium">Nota</label>
        <Textarea
          v-model="formNote"
          rows="3"
          autoResize
          placeholder="Lo que quieras recordar de este lugar…"
        />
      </div>
      <p v-if="place?.auto" class="text-xs text-slate-400">
        <i class="pi pi-info-circle" /> Añadido automáticamente desde el viaje
        "{{ place.origin }}".
      </p>
    </div>
    <template #footer>
      <Button label="Cancelar" severity="secondary" text @click="visible = false" />
      <Button :label="place ? 'Guardar' : 'Añadir'" @click="save" />
    </template>
  </Dialog>
</template>
