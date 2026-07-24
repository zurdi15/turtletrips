<script setup lang="ts">
import { onMounted, ref } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Popover from 'primevue/popover'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import type { Traveler } from '../api/types'
import { CATEGORY_PALETTE } from '../constants'
import { useTravelersStore } from '../stores/travelers'

const travelers = useTravelersStore()
const confirm = useConfirm()
const toast = useToast()

const newName = ref('')
const editingId = ref<number | null>(null)
const editingName = ref('')
const colorTargetId = ref<number | null>(null)
const colorPopover = ref()

onMounted(() => travelers.load(true))

function openColorPicker(event: Event, id: number) {
  colorTargetId.value = id
  colorPopover.value?.toggle(event)
}

async function pickColor(color: string) {
  if (colorTargetId.value == null) return
  await travelers.update(colorTargetId.value, { color })
  colorPopover.value?.hide()
}

async function add() {
  const name = newName.value.trim()
  if (!name) return
  try {
    await travelers.create(name, CATEGORY_PALETTE[travelers.items.length % CATEGORY_PALETTE.length])
    newName.value = ''
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: String(err), life: 4000 })
  }
}

function startRename(traveler: Traveler) {
  editingId.value = traveler.id
  editingName.value = traveler.name
}

async function confirmRename() {
  if (editingId.value == null || !editingName.value.trim()) return
  try {
    await travelers.update(editingId.value, { name: editingName.value.trim() })
    editingId.value = null
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: String(err), life: 4000 })
  }
}

function remove(traveler: Traveler) {
  confirm.require({
    message: `¿Eliminar a "${traveler.name}"? Se quitará de todos los viajes y sus gastos quedarán sin pagador.`,
    header: 'Eliminar viajero',
    icon: 'pi pi-exclamation-triangle',
    rejectProps: { label: 'Cancelar', severity: 'secondary', outlined: true },
    acceptProps: { label: 'Eliminar', severity: 'danger' },
    accept: () => travelers.remove(traveler.id),
  })
}
</script>

<template>
  <div class="max-w-2xl mx-auto">
    <div class="flex items-center gap-2 mb-6">
      <h1 class="text-2xl font-bold text-slate-800">Viajeros</h1>
      <button
        class="text-slate-400 hover:text-slate-600 transition-colors"
        v-tooltip.bottom="
          'Globales y reutilizables: créalos una vez y asócialos a cualquier viaje para marcar quién pagó cada gasto. No son cuentas de usuario.'
        "
        aria-label="Información sobre los viajeros"
      >
        <i class="pi pi-info-circle" />
      </button>
    </div>

    <div class="bg-white rounded-xl border border-slate-200 p-5">
      <ul class="flex flex-col gap-1.5 mb-4">
        <li
          v-for="traveler in travelers.items"
          :key="traveler.id"
          class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-slate-50 group"
        >
          <button
            class="w-5 h-5 rounded-full shrink-0 ring-1 ring-slate-200 hover:scale-110 transition-transform"
            :style="{ background: traveler.color ?? '#94a3b8' }"
            v-tooltip.top="'Cambiar color'"
            @click="openColorPicker($event, traveler.id)"
          />
          <template v-if="editingId === traveler.id">
            <InputText
              v-model="editingName"
              size="small"
              class="flex-1"
              autofocus
              @keyup.enter="confirmRename"
              @keyup.escape="editingId = null"
            />
            <Button icon="pi pi-check" text size="small" @click="confirmRename" />
            <Button icon="pi pi-times" text size="small" severity="secondary" @click="editingId = null" />
          </template>
          <template v-else>
            <span class="flex-1 text-slate-700 font-medium">{{ traveler.name }}</span>
            <div class="flex gap-1 hover-actions">
              <Button icon="pi pi-pencil" text size="small" severity="secondary" @click="startRename(traveler)" />
              <Button icon="pi pi-trash" text size="small" severity="danger" @click="remove(traveler)" />
            </div>
          </template>
        </li>
        <li v-if="!travelers.items.length" class="text-sm text-slate-400 px-3 py-4 text-center">
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

    <Popover ref="colorPopover">
      <div class="grid grid-cols-6 gap-2 p-1">
        <button
          v-for="color in CATEGORY_PALETTE"
          :key="color"
          class="w-6 h-6 rounded-full ring-1 ring-slate-200 hover:scale-110 transition-transform"
          :style="{ background: color }"
          @click="pickColor(color)"
        />
      </div>
    </Popover>
  </div>
</template>
