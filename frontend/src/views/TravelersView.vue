<script setup lang="ts">
import { onMounted, ref } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import PageHeader from '../components/ui/PageHeader.vue'
import EditableListItem from '../components/ui/EditableListItem.vue'
import ColorSwatchPopover from '../components/ui/ColorSwatchPopover.vue'
import type { Traveler } from '../api/types'
import { CATEGORY_PALETTE } from '../theme'
import { FALLBACK_CATEGORY_COLOR } from '../stores/categories'
import { useTravelersStore } from '../stores/travelers'
import { useConfirmDelete } from '../composables/useConfirmDelete'
import { useNotify } from '../composables/useNotify'

const travelers = useTravelersStore()
const confirmAction = useConfirmDelete()
const notify = useNotify()

const newName = ref('')
const colorTargetId = ref<number | null>(null)
const colorPopover = ref<InstanceType<typeof ColorSwatchPopover>>()

onMounted(() => travelers.load(true))

function openColorPicker(event: Event, id: number) {
  colorTargetId.value = id
  colorPopover.value?.toggle(event)
}

async function pickColor(color: string) {
  if (colorTargetId.value == null) return
  await travelers.update(colorTargetId.value, { color })
}

async function add() {
  const name = newName.value.trim()
  if (!name) return
  try {
    await travelers.create(name, CATEGORY_PALETTE[travelers.items.length % CATEGORY_PALETTE.length])
    newName.value = ''
  } catch (err) {
    notify.error('Error al añadir', err)
  }
}

async function rename(traveler: Traveler, name: string) {
  try {
    await travelers.update(traveler.id, { name })
  } catch (err) {
    notify.error('Error al renombrar', err)
  }
}

function remove(traveler: Traveler) {
  confirmAction({
    message: `¿Eliminar a "${traveler.name}"? Se quitará de todos los viajes y sus gastos quedarán sin pagador.`,
    header: 'Eliminar viajero',
    accept: () => travelers.remove(traveler.id),
  })
}
</script>

<template>
  <div class="max-w-2xl mx-auto">
    <PageHeader
      title="Viajeros"
      info="Globales y reutilizables: créalos una vez y asócialos a cualquier viaje para marcar quién pagó cada gasto. No son cuentas de usuario."
      class="mb-6"
    />

    <div class="bg-surface rounded-card border border-line p-5">
      <ul class="tt-stagger flex flex-col gap-1.5 mb-4">
        <EditableListItem
          v-for="traveler in travelers.items"
          :key="traveler.id"
          :name="traveler.name"
          :color="traveler.color"
          :colorFallback="FALLBACK_CATEGORY_COLOR"
          @rename="(name) => rename(traveler, name)"
          @remove="remove(traveler)"
          @pick-color="(event) => openColorPicker(event, traveler.id)"
        />
        <li v-if="!travelers.items.length" class="text-sm text-ink-faint px-3 py-4 text-center">
          Sin viajeros todavía: añade el primero abajo
        </li>
      </ul>
      <div class="flex gap-2">
        <InputText
          v-model="newName"
          placeholder="Nuevo viajero…"
          class="flex-1 min-w-0"
          @keyup.enter="add"
        />
        <Button
          label="Añadir"
          icon="pi pi-plus"
          class="shrink-0 max-sm:[&_.p-button-label]:hidden"
          @click="add"
        />
      </div>
    </div>

    <ColorSwatchPopover ref="colorPopover" @select="pickColor" />
  </div>
</template>
