<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import EmptyState from '../components/EmptyState.vue'
import PageHeader from '../components/ui/PageHeader.vue'
import PackingAddBar from '../components/packing/PackingAddBar.vue'
import PackingCategoryCard from '../components/packing/PackingCategoryCard.vue'
import TemplateList from '../components/packing/TemplateList.vue'
import TemplateItemRow from '../components/packing/TemplateItemRow.vue'
import type { PackingTemplateItem } from '../api/types'
import { usePackingTemplatesStore } from '../stores/packingTemplates'
import { useCategoriesStore } from '../stores/categories'
import { useConfirmDelete } from '../composables/useConfirmDelete'
import { useNotify } from '../composables/useNotify'
import { groupPackingItems } from '../utils/packing'

const store = usePackingTemplatesStore()
const categories = useCategoriesStore()
const confirmAction = useConfirmDelete()
const notify = useNotify()

const renaming = ref(false)
const renameValue = ref('')

onMounted(() => {
  store.load()
  categories.load('packing')
})

const categoryOptions = computed(() =>
  categories.packing.map((c) => ({ value: c.name, label: c.name })),
)

const grouped = computed(() =>
  groupPackingItems(
    store.detail?.items ?? [],
    categories.packing.map((c) => c.name),
    (name) => categories.colorOf('packing', name),
  ),
)

async function createTemplate(name: string) {
  try {
    const template = await store.create(name)
    await store.select(template.id)
  } catch (err) {
    notify.error('Error al crear', err)
  }
}

async function confirmRename() {
  if (!store.detail || !renameValue.value.trim()) return
  try {
    await store.rename(store.detail.id, renameValue.value.trim())
    renaming.value = false
  } catch (err) {
    notify.error('Error al renombrar', err)
  }
}

function removeTemplate() {
  if (!store.detail) return
  confirmAction({
    message: `¿Eliminar la plantilla "${store.detail.name}"? Las maletas ya aplicadas en viajes no se tocan.`,
    header: 'Eliminar plantilla',
    accept: () => store.remove(store.detail!.id),
  })
}

async function addItem(payload: { name: string; category: string; url: string | null }) {
  if (!store.detail) return
  try {
    await store.addItem(payload)
  } catch (err) {
    notify.error('Error al añadir', err)
    throw err // PackingAddBar conserva el texto si falla
  }
}

function saveItem(item: PackingTemplateItem, payload: { name: string; category: string; url: string | null }) {
  store.updateItem(item.id, payload)
}
</script>

<template>
  <div>
    <PageHeader
      title="Maletas"
      info="Plantillas de maleta reutilizables. Al aplicarlas en un viaje se copian: puedes modificar la maleta del viaje sin tocar la plantilla, y desde el viaje también puedes guardar los cambios de vuelta a la plantilla."
      class="mb-5"
    />

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
      <!-- lista de plantillas -->
      <TemplateList
        :templates="store.templates"
        :selectedId="store.detail?.id ?? null"
        :loading="store.loading"
        @select="store.select"
        @create="createTemplate"
      />

      <!-- detalle -->
      <div class="lg:col-span-2">
        <EmptyState
          v-if="!store.detail"
          icon="pi pi-briefcase"
          title="Elige una plantilla"
          subtitle="Selecciona una maleta de la lista o crea una nueva para editar su contenido"
        />
        <div v-else class="bg-white rounded-xl border border-slate-200 p-5">
          <div class="flex items-center gap-2 mb-4">
            <template v-if="renaming">
              <InputText
                v-model="renameValue"
                class="flex-1"
                autofocus
                @keyup.enter="confirmRename"
                @keyup.escape="renaming = false"
              />
              <Button icon="pi pi-check" text @click="confirmRename" />
              <Button icon="pi pi-times" text severity="secondary" @click="renaming = false" />
            </template>
            <template v-else>
              <h2 class="text-lg font-semibold text-slate-800 flex-1">{{ store.detail.name }}</h2>
              <Button
                icon="pi pi-pencil"
                text
                size="small"
                severity="secondary"
                v-tooltip.top="'Renombrar'"
                @click="renaming = true; renameValue = store.detail.name"
              />
              <Button
                icon="pi pi-trash"
                text
                size="small"
                severity="danger"
                v-tooltip.top="'Eliminar plantilla'"
                @click="removeTemplate"
              />
            </template>
          </div>

          <PackingAddBar
            placeholder="Añadir elemento…"
            :categoryOptions="categoryOptions"
            :onAdd="addItem"
            class="mb-4"
          />

          <p v-if="!store.detail.items.length" class="text-sm text-slate-400 py-4 text-center">
            Plantilla vacía: añade elementos aquí o guárdala desde la maleta de un viaje.
          </p>

          <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4 items-start">
            <PackingCategoryCard
              v-for="group in grouped"
              :key="group.name"
              :name="group.name"
              :color="group.color"
              :count="String(group.items.length)"
              size="sm"
            >
              <TemplateItemRow
                v-for="item in group.items"
                :key="item.id"
                :item="item"
                :categoryOptions="categoryOptions"
                @save="(payload) => saveItem(item, payload)"
                @remove="store.removeItem(item.id)"
              />
            </PackingCategoryCard>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
