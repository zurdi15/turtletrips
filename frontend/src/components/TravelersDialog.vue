<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import Dialog from 'primevue/dialog'
import AutoComplete from 'primevue/autocomplete'
import Button from 'primevue/button'
import { useToast } from 'primevue/usetoast'
import type { Traveler } from '../api/types'
import { MEMBER_COLORS } from '../constants'
import { useTripsStore } from '../stores/trips'
import { useTravelersStore } from '../stores/travelers'

const props = defineProps<{ tripId: number }>()
const visible = defineModel<boolean>('visible', { required: true })

const toast = useToast()
const trips = useTripsStore()
const travelers = useTravelersStore()

const query = ref<string | Traveler>('')
const suggestions = ref<Traveler[]>([])

onMounted(() => travelers.load())

const inTrip = computed(() => new Set((trips.current?.travelers ?? []).map((t) => t.id)))

function search(text: string) {
  const q = text.trim().toLowerCase()
  suggestions.value = travelers.items.filter(
    (t) => !inTrip.value.has(t.id) && (!q || t.name.toLowerCase().includes(q)),
  )
}

async function addExisting(traveler: Traveler) {
  try {
    await trips.addTravelerToTrip(props.tripId, traveler.id)
    query.value = ''
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: String(err), life: 4000 })
  }
}

async function addByName() {
  const raw = typeof query.value === 'string' ? query.value.trim() : ''
  if (!raw) return
  try {
    const color = MEMBER_COLORS[travelers.items.length % MEMBER_COLORS.length]
    const traveler = await travelers.create(raw, color)
    await trips.addTravelerToTrip(props.tripId, traveler.id)
    query.value = ''
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: String(err), life: 4000 })
  }
}

async function removeFromTrip(travelerId: number) {
  await trips.removeTravelerFromTrip(props.tripId, travelerId)
}

async function setColor(traveler: Traveler, color: string) {
  await travelers.update(traveler.id, { color })
  if (trips.current) {
    const inList = trips.current.travelers.find((t) => t.id === traveler.id)
    if (inList) inList.color = color
  }
}
</script>

<template>
  <Dialog v-model:visible="visible" modal class="w-full max-w-md mx-4">
    <template #header>
      <div class="flex items-center gap-2">
        <span class="p-dialog-title">Viajeros</span>
        <button
          class="text-slate-400 hover:text-slate-600 transition-colors"
          v-tooltip.bottom="
            'Los viajeros son globales: se guardan una vez y se reutilizan en cualquier viaje para marcar quién pagó cada gasto. Se gestionan en la sección Viajeros. No son cuentas de usuario.'
          "
          aria-label="Información sobre los viajeros"
        >
          <i class="pi pi-info-circle" />
        </button>
      </div>
    </template>
    <ul class="flex flex-col gap-2 mb-4">
      <li
        v-for="traveler in trips.current?.travelers ?? []"
        :key="traveler.id"
        class="flex items-center gap-3 p-2 rounded-lg border border-slate-200"
      >
        <span
          class="w-3 h-3 rounded-full shrink-0"
          :style="{ background: traveler.color ?? '#94a3b8' }"
        />
        <span class="flex-1 font-medium">{{ traveler.name }}</span>
        <div class="flex gap-1">
          <button
            v-for="color in MEMBER_COLORS"
            :key="color"
            class="w-4 h-4 rounded-full border border-white ring-1 ring-slate-200 hover:scale-110 transition-transform"
            :style="{ background: color }"
            @click="setColor(traveler, color)"
          />
        </div>
        <Button
          icon="pi pi-times"
          severity="danger"
          text
          size="small"
          v-tooltip.left="'Quitar de este viaje'"
          @click="removeFromTrip(traveler.id)"
        />
      </li>
      <li v-if="!trips.current?.travelers.length" class="text-sm text-slate-400 text-center py-2">
        Sin viajeros en este viaje
      </li>
    </ul>
    <div class="flex gap-2">
      <AutoComplete
        v-model="query"
        :suggestions="suggestions"
        optionLabel="name"
        placeholder="Busca un viajero o escribe uno nuevo"
        class="flex-1"
        dropdown
        @complete="(e) => search(e.query)"
        @item-select="(e) => addExisting(e.value)"
        @keyup.enter="addByName"
      />
      <Button
        label="Añadir"
        icon="pi pi-plus"
        class="shrink-0 max-sm:[&_.p-button-label]:hidden"
        @click="addByName"
      />
    </div>
  </Dialog>
</template>
