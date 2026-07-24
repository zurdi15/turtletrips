<script setup lang="ts">
import { computed, ref } from 'vue'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import Textarea from 'primevue/textarea'
import FormDialog from '../ui/FormDialog.vue'
import FormField from '../ui/FormField.vue'
import type { WorldPlace, WorldPlaceKind } from '../../api/types'
import { COUNTRY_OPTIONS } from '../../countries'
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

const store = useWorldPlacesStore()

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
  validate: () => (formName.value.trim() ? null : 'El nombre es obligatorio'),
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
    :header="place ? 'Editar lugar' : 'Añadir al mapa'"
    width="md"
    :saving="saving"
    :saveLabel="place ? 'Guardar' : 'Añadir'"
    @save="save"
  >
    <FormField label="Nombre" required>
      <InputText v-model="formName" autofocus />
    </FormField>
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
      <FormField label="Tipo">
        <Select v-model="formKind" :options="kindOptions" optionLabel="label" optionValue="value" />
      </FormField>
      <FormField v-if="formKind !== 'country'" label="País">
        <Select
          v-model="formCountry"
          :options="dialogCountryOptions"
          optionLabel="label"
          optionValue="code"
          filter
        />
      </FormField>
    </div>
    <FormField label="Nota">
      <Textarea
        v-model="formNote"
        rows="3"
        autoResize
        placeholder="Lo que quieras recordar de este lugar…"
      />
    </FormField>
    <p v-if="place?.auto" class="text-xs text-slate-400">
      <i class="pi pi-info-circle" /> Añadido automáticamente desde el viaje
      "{{ place.origin }}".
    </p>
  </FormDialog>
</template>
