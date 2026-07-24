<script setup lang="ts">
import { onMounted, ref } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Popover from 'primevue/popover'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import type { Category } from '../api/types'
import { CATEGORY_PALETTE } from '../constants'
import { useCategoriesStore, FALLBACK_CATEGORY_COLOR } from '../stores/categories'

const categories = useCategoriesStore()
const confirm = useConfirm()
const toast = useToast()

onMounted(() => {
  categories.load('expense')
  categories.load('packing')
})

const newNames = ref<Record<string, string>>({ expense: '', packing: '' })
const editingId = ref<number | null>(null)
const editingName = ref('')

const colorTarget = ref<{ kind: 'expense' | 'packing'; id: number } | null>(null)
const colorPopover = ref()

function openColorPicker(event: Event, kind: 'expense' | 'packing', id: number) {
  colorTarget.value = { kind, id }
  colorPopover.value?.toggle(event)
}

async function pickColor(color: string) {
  if (!colorTarget.value) return
  try {
    await categories.update(colorTarget.value.id, colorTarget.value.kind, { color })
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: String(err), life: 4000 })
  }
  colorPopover.value?.hide()
}

async function addCategory(kind: 'expense' | 'packing') {
  const name = newNames.value[kind].trim()
  if (!name) return
  try {
    const color = CATEGORY_PALETTE[categories[kind].length % CATEGORY_PALETTE.length]
    await categories.create(kind, name, color)
    newNames.value[kind] = ''
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: String(err), life: 4000 })
  }
}

function startRename(category: Category) {
  editingId.value = category.id
  editingName.value = category.name
}

async function confirmRename(kind: 'expense' | 'packing') {
  if (editingId.value == null || !editingName.value.trim()) return
  try {
    await categories.update(editingId.value, kind, { name: editingName.value.trim() })
    editingId.value = null
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: String(err), life: 4000 })
  }
}

function removeCategory(kind: 'expense' | 'packing', category: Category) {
  confirm.require({
    message: `¿Eliminar la categoría "${category.name}"? Los elementos existentes conservan el nombre.`,
    header: 'Eliminar categoría',
    icon: 'pi pi-exclamation-triangle',
    rejectProps: { label: 'Cancelar', severity: 'secondary', outlined: true },
    acceptProps: { label: 'Eliminar', severity: 'danger' },
    accept: () => categories.remove(category.id, kind),
  })
}

const sections: { kind: 'expense' | 'packing'; title: string; hint: string }[] = [
  {
    kind: 'expense',
    title: 'Categorías de gastos',
    hint: 'Renombrar una categoría actualiza también los gastos existentes.',
  },
  {
    kind: 'packing',
    title: 'Categorías de maleta',
    hint: 'Se usan para agrupar los elementos de las maletas y plantillas.',
  },
]
</script>

<template>
  <div class="max-w-3xl mx-auto">
    <h1 class="text-2xl font-bold text-slate-800 mb-6">Ajustes</h1>

    <div class="flex flex-col gap-6">
      <section
        v-for="section in sections"
        :key="section.kind"
        class="bg-white rounded-xl border border-slate-200 p-5"
      >
        <h2 class="font-semibold text-slate-700 mb-1">{{ section.title }}</h2>
        <p class="text-xs text-slate-400 mb-4">{{ section.hint }}</p>
        <ul class="flex flex-col gap-1.5 mb-4">
          <li
            v-for="category in categories[section.kind]"
            :key="category.id"
            class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-slate-50 group"
          >
            <button
              class="w-5 h-5 rounded-full shrink-0 ring-1 ring-slate-200 hover:scale-110 transition-transform"
              :style="{ background: category.color ?? FALLBACK_CATEGORY_COLOR }"
              v-tooltip.top="'Cambiar color'"
              @click="openColorPicker($event, section.kind, category.id)"
            />
            <template v-if="editingId === category.id">
              <InputText
                v-model="editingName"
                size="small"
                class="flex-1"
                autofocus
                @keyup.enter="confirmRename(section.kind)"
                @keyup.escape="editingId = null"
              />
              <Button icon="pi pi-check" text size="small" @click="confirmRename(section.kind)" />
              <Button icon="pi pi-times" text size="small" severity="secondary" @click="editingId = null" />
            </template>
            <template v-else>
              <span class="flex-1 text-slate-700">{{ category.name }}</span>
              <div class="flex gap-1 hover-actions">
                <Button icon="pi pi-pencil" text size="small" severity="secondary" @click="startRename(category)" />
                <Button
                  icon="pi pi-trash"
                  text
                  size="small"
                  severity="danger"
                  @click="removeCategory(section.kind, category)"
                />
              </div>
            </template>
          </li>
        </ul>
        <div class="flex gap-2">
          <InputText
            v-model="newNames[section.kind]"
            placeholder="Nueva categoría…"
            class="flex-1 min-w-0"
            @keyup.enter="addCategory(section.kind)"
          />
          <Button
            label="Añadir"
            icon="pi pi-plus"
            class="shrink-0 max-sm:[&_.p-button-label]:hidden"
            @click="addCategory(section.kind)"
          />
        </div>
      </section>
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
