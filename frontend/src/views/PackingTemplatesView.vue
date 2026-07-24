<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import EmptyState from '../components/EmptyState.vue'
import type { PackingTemplateItem } from '../api/types'
import { usePackingTemplatesStore } from '../stores/packingTemplates'
import { useCategoriesStore, FALLBACK_CATEGORY_COLOR } from '../stores/categories'
import { groupPackingItems } from '../utils/packing'

const store = usePackingTemplatesStore()
const categories = useCategoriesStore()
const confirm = useConfirm()
const toast = useToast()

const newTemplateName = ref('')
const renaming = ref(false)
const renameValue = ref('')

const newItemName = ref('')
const newItemCategory = ref('Ropa')
const newItemUrl = ref('')
const showUrlField = ref(false)

const editingItem = ref<PackingTemplateItem | null>(null)
const editName = ref('')
const editCategory = ref('')
const editUrl = ref('')

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

async function createTemplate() {
  const name = newTemplateName.value.trim()
  if (!name) return
  try {
    const template = await store.create(name)
    newTemplateName.value = ''
    await store.select(template.id)
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: String(err), life: 4000 })
  }
}

async function confirmRename() {
  if (!store.detail || !renameValue.value.trim()) return
  try {
    await store.rename(store.detail.id, renameValue.value.trim())
    renaming.value = false
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: String(err), life: 4000 })
  }
}

function removeTemplate() {
  if (!store.detail) return
  confirm.require({
    message: `¿Eliminar la plantilla "${store.detail.name}"? Las maletas ya aplicadas en viajes no se tocan.`,
    header: 'Eliminar plantilla',
    icon: 'pi pi-exclamation-triangle',
    rejectProps: { label: 'Cancelar', severity: 'secondary', outlined: true },
    acceptProps: { label: 'Eliminar', severity: 'danger' },
    accept: () => store.remove(store.detail!.id),
  })
}

async function addItem() {
  const name = newItemName.value.trim()
  if (!name || !store.detail) return
  try {
    await store.addItem({
      name,
      category: newItemCategory.value,
      url: newItemUrl.value.trim() || null,
    })
    newItemName.value = ''
    newItemUrl.value = ''
    showUrlField.value = false
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: String(err), life: 4000 })
  }
}

function openEdit(item: PackingTemplateItem) {
  editingItem.value = item
  editName.value = item.name
  editCategory.value = item.category
  editUrl.value = item.url ?? ''
}

async function saveEdit() {
  if (!editingItem.value || !editName.value.trim()) return
  await store.updateItem(editingItem.value.id, {
    name: editName.value.trim(),
    category: editCategory.value,
    url: editUrl.value.trim() || null,
  })
  editingItem.value = null
}
</script>

<template>
  <div>
    <div class="flex items-center gap-2 mb-5">
      <h1 class="text-2xl font-bold text-slate-800">Maletas</h1>
      <button
        class="text-slate-400 hover:text-slate-600 transition-colors"
        v-tooltip.bottom="
          'Plantillas de maleta reutilizables. Al aplicarlas en un viaje se copian: puedes modificar la maleta del viaje sin tocar la plantilla, y desde el viaje también puedes guardar los cambios de vuelta a la plantilla.'
        "
        aria-label="Información sobre las maletas"
      >
        <i class="pi pi-info-circle" />
      </button>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
      <!-- lista de plantillas -->
      <div class="bg-white rounded-xl border border-slate-200 p-4">
        <ul class="tt-stagger flex flex-col gap-1 mb-4">
          <li v-for="template in store.templates" :key="template.id">
            <button
              class="w-full text-left px-3 py-2 rounded-lg flex items-center gap-2 transition-colors"
              :class="
                store.detail?.id === template.id
                  ? 'bg-slate-100 text-slate-900 font-medium'
                  : 'text-slate-600 hover:bg-slate-50'
              "
              @click="store.select(template.id)"
            >
              <i class="pi pi-briefcase text-xs text-slate-400" />
              <span class="flex-1">{{ template.name }}</span>
              <span class="text-xs text-slate-400">{{ template.item_count }}</span>
            </button>
          </li>
          <li v-if="!store.templates.length && !store.loading" class="text-sm text-slate-400 px-3 py-2">
            Sin plantillas todavía
          </li>
        </ul>
        <div class="flex gap-2">
          <InputText
            v-model="newTemplateName"
            placeholder="Nueva plantilla…"
            class="flex-1"
            size="small"
            @keyup.enter="createTemplate"
          />
          <Button icon="pi pi-plus" size="small" @click="createTemplate" />
        </div>
      </div>

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

          <div class="flex flex-wrap items-center gap-2 mb-4">
            <InputText
              v-model="newItemName"
              placeholder="Añadir elemento…"
              class="w-full sm:w-52"
              @keyup.enter="addItem"
            />
            <Select
              v-model="newItemCategory"
              :options="categoryOptions"
              optionLabel="label"
              optionValue="value"
              class="flex-1 sm:flex-none sm:w-40"
            />
            <Button
              icon="pi pi-link"
              severity="secondary"
              :outlined="!showUrlField"
              v-tooltip.top="'Añadir enlace de compra'"
              @click="showUrlField = !showUrlField"
            />
            <InputText
              v-if="showUrlField"
              v-model="newItemUrl"
              placeholder="https://…"
              class="w-full sm:w-56"
              @keyup.enter="addItem"
            />
            <Button
              label="Añadir"
              icon="pi pi-plus"
              class="shrink-0 max-sm:[&_.p-button-label]:hidden"
              @click="addItem"
            />
          </div>

          <p v-if="!store.detail.items.length" class="text-sm text-slate-400 py-4 text-center">
            Plantilla vacía: añade elementos aquí o guárdala desde la maleta de un viaje.
          </p>

          <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4 items-start">
            <div
              v-for="group in grouped"
              :key="group.name"
              class="rounded-lg border border-slate-200 overflow-hidden"
            >
              <div
                class="px-3 py-2 border-b border-slate-100 flex items-center gap-2 text-sm"
                :style="{ borderTop: `3px solid ${group.color ?? FALLBACK_CATEGORY_COLOR}` }"
              >
                <span class="font-semibold text-slate-700">{{ group.name }}</span>
                <span class="text-xs text-slate-400">{{ group.items.length }}</span>
              </div>
              <ul>
                <li
                  v-for="item in group.items"
                  :key="item.id"
                  class="flex flex-wrap items-center gap-2 px-3 py-1.5 border-b border-slate-50 last:border-b-0 hover:bg-slate-50 group/item text-sm"
                >
                  <template v-if="editingItem?.id === item.id">
                    <InputText v-model="editName" size="small" class="flex-1" @keyup.enter="saveEdit" />
                    <Select
                      v-model="editCategory"
                      :options="categoryOptions"
                      optionLabel="label"
                      optionValue="value"
                      size="small"
                      class="w-32"
                    />
                    <InputText v-model="editUrl" size="small" placeholder="https://…" class="w-32" />
                    <Button icon="pi pi-check" text size="small" @click="saveEdit" />
                    <Button icon="pi pi-times" text size="small" severity="secondary" @click="editingItem = null" />
                  </template>
                  <template v-else>
                    <span class="flex-1 text-slate-700">
                      {{ item.name }}
                      <a
                        v-if="item.url"
                        :href="item.url"
                        target="_blank"
                        rel="noopener"
                        class="ml-1 text-sky-600 hover:underline text-xs"
                        v-tooltip.top="'Enlace de compra'"
                      >
                        <i class="pi pi-shopping-cart" />
                      </a>
                    </span>
                    <div class="flex gap-1 hover-actions">
                      <Button icon="pi pi-pencil" text size="small" severity="secondary" @click="openEdit(item)" />
                      <Button icon="pi pi-trash" text size="small" severity="danger" @click="store.removeItem(item.id)" />
                    </div>
                  </template>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
