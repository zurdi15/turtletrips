<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import SelectButton from 'primevue/selectbutton'
import PageHeader from '../components/ui/PageHeader.vue'
import EditableListItem from '../components/ui/EditableListItem.vue'
import ColorSwatchPopover from '../components/ui/ColorSwatchPopover.vue'
import UploadButton from '../components/ui/UploadButton.vue'
import { api, API_BASE } from '../api/client'
import type { Category } from '../api/types'
import { CATEGORY_PALETTE } from '../constants'
import { useCategoriesStore, FALLBACK_CATEGORY_COLOR } from '../stores/categories'
import { useConfirmDelete } from '../composables/useConfirmDelete'
import { useNotify } from '../composables/useNotify'
import { useTheme } from '../composables/useTheme'

const categories = useCategoriesStore()
const confirmAction = useConfirmDelete()
const notify = useNotify()

// ---- apariencia (tema claro/oscuro) ----

const { isDark, toggle } = useTheme()
const theme = computed<'light' | 'dark'>({
  get: () => (isDark.value ? 'dark' : 'light'),
  set: (v) => {
    if ((v === 'dark') !== isDark.value) toggle()
  },
})
const themeOptions = [
  { value: 'light', label: 'Claro', icon: 'pi pi-sun' },
  { value: 'dark', label: 'Oscuro', icon: 'pi pi-moon' },
]

// ---- copia de seguridad ----

const backupExportUrl = `${API_BASE}/backup/export`
const restoring = ref(false)

function onRestoreFilePicked(file: File) {
  confirmAction({
    message:
      'Esto reemplazará TODOS los datos actuales (viajes, gastos, adjuntos…) ' +
      'por los de la copia. Esta acción no se puede deshacer.',
    header: 'Restaurar copia de seguridad',
    acceptLabel: 'Restaurar',
    accept: async () => {
      restoring.value = true
      try {
        const form = new FormData()
        form.append('file', file)
        const result = await api.upload<{ trips: number }>('/backup/restore', form)
        notify.success(`Copia restaurada (${result.trips} viajes)`)
        // todas las stores quedan obsoletas tras el restore
        setTimeout(() => window.location.reload(), 800)
      } catch (err) {
        notify.error('No se pudo restaurar', err)
        restoring.value = false
      }
    },
  })
}

onMounted(() => {
  categories.load('expense')
  categories.load('packing')
})

const newNames = ref<Record<string, string>>({ expense: '', packing: '' })

const colorTarget = ref<{ kind: 'expense' | 'packing'; id: number } | null>(null)
const colorPopover = ref<InstanceType<typeof ColorSwatchPopover>>()

function openColorPicker(event: Event, kind: 'expense' | 'packing', id: number) {
  colorTarget.value = { kind, id }
  colorPopover.value?.toggle(event)
}

async function pickColor(color: string) {
  if (!colorTarget.value) return
  try {
    await categories.update(colorTarget.value.id, colorTarget.value.kind, { color })
  } catch (err) {
    notify.error('Error al cambiar el color', err)
  }
}

async function addCategory(kind: 'expense' | 'packing') {
  const name = newNames.value[kind].trim()
  if (!name) return
  try {
    const color = CATEGORY_PALETTE[categories[kind].length % CATEGORY_PALETTE.length]
    await categories.create(kind, name, color)
    newNames.value[kind] = ''
  } catch (err) {
    notify.error('Error al añadir', err)
  }
}

async function renameCategory(kind: 'expense' | 'packing', category: Category, name: string) {
  try {
    await categories.update(category.id, kind, { name })
  } catch (err) {
    notify.error('Error al renombrar', err)
  }
}

function removeCategory(kind: 'expense' | 'packing', category: Category) {
  confirmAction({
    message: `¿Eliminar la categoría "${category.name}"? Los elementos existentes conservan el nombre.`,
    header: 'Eliminar categoría',
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
    <PageHeader title="Ajustes" class="mb-6" />

    <div class="flex flex-col gap-6">
      <section class="bg-surface rounded-card border border-line p-5">
        <h2 class="font-semibold text-ink mb-1">Apariencia</h2>
        <p class="text-xs text-ink-faint mb-4">Tema de la interfaz.</p>
        <SelectButton
          v-model="theme"
          :options="themeOptions"
          optionLabel="label"
          optionValue="value"
          :allowEmpty="false"
          aria-label="Tema de la interfaz"
        >
          <template #option="{ option }">
            <span class="flex items-center gap-2">
              <i :class="option.icon" />
              {{ option.label }}
            </span>
          </template>
        </SelectButton>
      </section>

      <section
        v-for="section in sections"
        :key="section.kind"
        class="bg-surface rounded-card border border-line p-5"
      >
        <h2 class="font-semibold text-ink mb-1">{{ section.title }}</h2>
        <p class="text-xs text-ink-faint mb-4">{{ section.hint }}</p>
        <ul class="flex flex-col gap-1.5 mb-4">
          <EditableListItem
            v-for="category in categories[section.kind]"
            :key="category.id"
            :name="category.name"
            :color="category.color"
            :colorFallback="FALLBACK_CATEGORY_COLOR"
            @rename="(name) => renameCategory(section.kind, category, name)"
            @remove="removeCategory(section.kind, category)"
            @pick-color="(event) => openColorPicker(event, section.kind, category.id)"
          />
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

      <section class="bg-surface rounded-card border border-line p-5">
        <h2 class="font-semibold text-ink mb-1">Copia de seguridad</h2>
        <p class="text-xs text-ink-faint mb-4">
          La copia incluye la base de datos completa y todos los adjuntos.
        </p>
        <div class="flex flex-wrap gap-2">
          <a :href="backupExportUrl" download>
            <Button label="Descargar copia" icon="pi pi-download" severity="secondary" outlined />
          </a>
          <UploadButton
            label="Restaurar desde copia…"
            icon="pi pi-upload"
            severity="danger"
            outlined
            accept=".zip,application/zip"
            :loading="restoring"
            @file="onRestoreFilePicked"
          />
        </div>
      </section>
    </div>

    <ColorSwatchPopover ref="colorPopover" @select="pickColor" />
  </div>
</template>
