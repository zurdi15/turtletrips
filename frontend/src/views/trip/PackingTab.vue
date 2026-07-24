<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import Checkbox from 'primevue/checkbox'
import Dialog from 'primevue/dialog'
import EmptyState from '../../components/EmptyState.vue'
import TabSkeleton from '../../components/TabSkeleton.vue'
import type { PackingItem, Trip } from '../../api/types'
import { usePackingStore } from '../../stores/packing'
import { useCategoriesStore, FALLBACK_CATEGORY_COLOR } from '../../stores/categories'
import { useConfirmDelete } from '../../composables/useConfirmDelete'
import { useNotify } from '../../composables/useNotify'
import { useTripTabData } from '../../composables/useTripTabData'
import { groupPackingItems } from '../../utils/packing'

const props = defineProps<{ trip: Trip }>()
const store = usePackingStore()
const categories = useCategoriesStore()
const confirmAction = useConfirmDelete()
const notify = useNotify()

// maleta activa: null = común, número = viajero
const activeTraveler = ref<number | null>(null)
const selectedTemplate = ref<number | null>(null)

const newName = ref('')
const newCategory = ref('Ropa')
const newUrl = ref('')
const showUrlField = ref(false)

const editing = ref<PackingItem | null>(null)
const editName = ref('')
const editCategory = ref('')
const editUrl = ref('')
const editTraveler = ref<number | null>(null)

const showSaveTemplate = ref(false)
const templateName = ref('')

useTripTabData(() => props.trip, {
  load(tripId) {
    store.load(tripId).then(syncSelectedTemplate)
    categories.load('packing')
  },
})

// al cambiar de maleta, refleja la plantilla que tiene asociada
function syncSelectedTemplate() {
  selectedTemplate.value = store.selectionFor(activeTraveler.value)
}
watch(activeTraveler, syncSelectedTemplate)
watch(() => store.selections, syncSelectedTemplate, { deep: true })

interface BagOption {
  travelerId: number | null
  label: string
  color: string | null
}

const bags = computed<BagOption[]>(() => [
  { travelerId: null, label: 'Común', color: null },
  ...props.trip.travelers.map((t) => ({ travelerId: t.id, label: t.name, color: t.color })),
])

function bagProgress(travelerId: number | null): { done: number; total: number } {
  const items = store.itemsFor(travelerId)
  return { done: items.filter((i) => i.checked).length, total: items.length }
}

const activeItems = computed(() => store.itemsFor(activeTraveler.value))

const activeProgress = computed(() => {
  const { done, total } = bagProgress(activeTraveler.value)
  return { done, total, pct: total ? Math.round((done / total) * 100) : 0 }
})

const activeBagLabel = computed(
  () => bags.value.find((b) => b.travelerId === activeTraveler.value)?.label ?? 'Común',
)

const categoryOptions = computed(() =>
  categories.packing.map((c) => ({ value: c.name, label: c.name })),
)

const bagMoveOptions = computed(() =>
  bags.value.map((b) => ({ value: b.travelerId, label: b.label })),
)

const templateOptions = computed(() =>
  store.templates.map((t) => ({ value: t.id, label: `${t.name} (${t.item_count})` })),
)

const activeTemplateName = computed(() => {
  const id = store.selectionFor(activeTraveler.value)
  return store.templates.find((t) => t.id === id)?.name ?? null
})

const grouped = computed(() =>
  groupPackingItems(
    activeItems.value,
    categories.packing.map((c) => c.name),
    (name) => categories.colorOf('packing', name),
  ),
)

async function addItem() {
  const name = newName.value.trim()
  if (!name) return
  try {
    await store.create({
      name,
      category: newCategory.value,
      url: newUrl.value.trim() || null,
      traveler_id: activeTraveler.value,
    })
    newName.value = ''
    newUrl.value = ''
    showUrlField.value = false
  } catch (err) {
    notify.error('Error al añadir', err)
  }
}

function openEdit(item: PackingItem) {
  editing.value = item
  editName.value = item.name
  editCategory.value = item.category
  editUrl.value = item.url ?? ''
  editTraveler.value = item.traveler_id
}

async function saveEdit() {
  if (!editing.value || !editName.value.trim()) return
  await store.update(editing.value.id, {
    name: editName.value.trim(),
    category: editCategory.value,
    url: editUrl.value.trim() || null,
    traveler_id: editTraveler.value,
  })
  editing.value = null
}

function removeItem(item: PackingItem) {
  confirmAction({
    message: `¿Eliminar "${item.name}" de la maleta?`,
    header: 'Eliminar elemento',
    accept: () => store.remove(item.id),
  })
}

async function applyTemplate() {
  if (selectedTemplate.value == null) return
  await store.applyTemplate(selectedTemplate.value, activeTraveler.value)
  notify.success(
    `Plantilla aplicada a la maleta de ${activeBagLabel.value}`,
    'Los cambios que hagas aquí no afectan a la plantilla',
  )
}

function syncTemplate() {
  if (selectedTemplate.value == null) return
  const template = store.templates.find((t) => t.id === selectedTemplate.value)
  confirmAction({
    message: `¿Sobrescribir la plantilla "${template?.name}" con los ${activeItems.value.length} elementos de la maleta de ${activeBagLabel.value}?`,
    header: 'Guardar cambios en la plantilla',
    icon: 'pi pi-sync',
    acceptLabel: 'Sobrescribir plantilla',
    acceptSeverity: undefined,
    accept: async () => {
      await store.syncTemplateFromTrip(selectedTemplate.value!, activeTraveler.value)
      notify.success('Plantilla actualizada')
    },
  })
}

async function saveTemplate() {
  const name = templateName.value.trim()
  if (!name) return
  try {
    await store.saveAsTemplate(name, activeTraveler.value)
    notify.success(`Plantilla "${name}" guardada`)
    showSaveTemplate.value = false
    templateName.value = ''
    syncSelectedTemplate()
  } catch (err) {
    notify.error('Error al guardar', err)
  }
}
</script>

<template>
  <div>
    <!-- selector de maleta: común + una por viajero -->
    <div class="flex flex-wrap items-center gap-2 mb-4">
      <button
        v-for="bag in bags"
        :key="bag.travelerId ?? 'common'"
        class="flex items-center gap-2 px-3.5 py-2 rounded-xl border transition-colors"
        :class="
          activeTraveler === bag.travelerId
            ? 'border-[var(--p-primary-color)] bg-[var(--p-primary-50)] text-slate-900'
            : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300'
        "
        @click="activeTraveler = bag.travelerId"
      >
        <span
          v-if="bag.color"
          class="w-2.5 h-2.5 rounded-full"
          :style="{ background: bag.color }"
        />
        <i v-else class="pi pi-briefcase text-xs text-slate-400" />
        <span class="font-medium">{{ bag.label }}</span>
        <span
          class="text-xs px-1.5 py-0.5 rounded-full"
          :class="
            bagProgress(bag.travelerId).total &&
            bagProgress(bag.travelerId).done === bagProgress(bag.travelerId).total
              ? 'bg-emerald-100 text-emerald-700'
              : 'bg-slate-100 text-slate-500'
          "
        >
          {{ bagProgress(bag.travelerId).done }}/{{ bagProgress(bag.travelerId).total }}
        </span>
      </button>
      <p v-if="!trip.travelers.length" class="text-xs text-slate-400 ml-2">
        Añade viajeros al viaje para que cada uno tenga su maleta
      </p>
    </div>

    <!-- barra de la maleta activa: plantilla + progreso -->
    <div class="bg-white rounded-xl border border-slate-200 p-4 mb-4">
      <div class="flex flex-wrap items-center gap-2">
        <span class="text-sm font-semibold text-slate-600 mr-1">
          Maleta de {{ activeBagLabel }}
        </span>
        <span v-if="activeTemplateName" class="text-xs px-2 py-0.5 rounded-full bg-sky-50 text-sky-700">
          <i class="pi pi-briefcase text-[10px]" /> plantilla: {{ activeTemplateName }}
        </span>
        <span class="flex-1" />
        <Select
          v-model="selectedTemplate"
          :options="templateOptions"
          optionLabel="label"
          optionValue="value"
          placeholder="Elegir plantilla…"
          class="w-full sm:w-52"
          size="small"
        />
        <Button
          v-if="selectedTemplate != null"
          label="Aplicar"
          icon="pi pi-download"
          severity="secondary"
          size="small"
          v-tooltip.bottom="'Copia los elementos a esta maleta; la plantilla no se toca'"
          @click="applyTemplate"
        />
        <Button
          v-if="selectedTemplate != null && activeItems.length"
          icon="pi pi-sync"
          severity="secondary"
          outlined
          size="small"
          v-tooltip.bottom="'Guardar esta maleta (con tus cambios) en la plantilla'"
          @click="syncTemplate"
        />
        <Button
          v-if="activeItems.length"
          label="Nueva plantilla"
          icon="pi pi-save"
          severity="secondary"
          outlined
          size="small"
          v-tooltip.bottom="'Guardar esta maleta como plantilla nueva'"
          @click="showSaveTemplate = true"
        />
      </div>
      <div v-if="activeProgress.total" class="mt-3">
        <div class="h-2 rounded-full bg-slate-100 overflow-hidden">
          <div
            class="h-full rounded-full bg-emerald-500 transition-all"
            :style="{ width: `${activeProgress.pct}%` }"
          />
        </div>
        <p class="text-xs text-slate-400 mt-1">
          {{ activeProgress.done }}/{{ activeProgress.total }} preparado · {{ activeProgress.pct }}%
        </p>
      </div>
    </div>

    <!-- añadir elemento a la maleta activa -->
    <div class="flex flex-wrap items-center gap-2 mb-5">
      <InputText
        v-model="newName"
        :placeholder="`Añadir a la maleta de ${activeBagLabel}…`"
        class="w-full sm:w-64"
        @keyup.enter="addItem"
      />
      <Select
        v-model="newCategory"
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
        v-model="newUrl"
        placeholder="https://… (enlace de compra)"
        class="w-full sm:w-64"
        @keyup.enter="addItem"
      />
      <Button
        label="Añadir"
        icon="pi pi-plus"
        class="shrink-0 max-sm:[&_.p-button-label]:hidden"
        @click="addItem"
      />
    </div>

    <TabSkeleton v-if="store.loading && !store.items.length" variant="list" :rows="8" />

    <EmptyState
      v-else-if="!store.loading && !activeItems.length"
      icon="pi pi-briefcase"
      :title="`La maleta de ${activeBagLabel} está vacía`"
      subtitle="Añade elementos o aplica una plantilla"
    />

    <div v-else class="tt-stagger grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 items-start">
      <div
        v-for="group in grouped"
        :key="group.name"
        class="bg-white rounded-xl border border-slate-200 overflow-hidden"
      >
        <div
          class="px-4 py-2.5 border-b border-slate-100 flex items-center gap-2"
          :style="{ borderTop: `3px solid ${group.color ?? FALLBACK_CATEGORY_COLOR}` }"
        >
          <span class="font-semibold text-slate-700">{{ group.name }}</span>
          <span class="text-xs text-slate-400">
            {{ group.items.filter((i) => i.checked).length }}/{{ group.items.length }}
          </span>
        </div>
        <ul>
          <li
            v-for="item in group.items"
            :key="item.id"
            class="flex items-center gap-3 px-4 py-2 border-b border-slate-50 last:border-b-0 hover:bg-slate-50 group/item"
          >
            <Checkbox
              :modelValue="item.checked"
              binary
              @update:modelValue="store.toggle(item)"
            />
            <span
              class="flex-1 transition-colors duration-200"
              :class="{ 'line-through text-slate-400': item.checked }"
            >
              {{ item.name }}
              <a
                v-if="item.url"
                :href="item.url"
                target="_blank"
                rel="noopener"
                class="ml-1 text-sky-600 hover:underline text-xs"
                v-tooltip.top="'Enlace de compra'"
                @click.stop
              >
                <i class="pi pi-shopping-cart" />
              </a>
            </span>
            <div class="flex gap-1 hover-actions">
              <Button icon="pi pi-pencil" text size="small" severity="secondary" @click="openEdit(item)" />
              <Button icon="pi pi-trash" text size="small" severity="danger" @click="removeItem(item)" />
            </div>
          </li>
        </ul>
      </div>
    </div>

    <!-- diálogo editar (permite mover entre maletas) -->
    <Dialog
      :visible="editing != null"
      modal
      header="Editar elemento"
      class="w-full max-w-md mx-4"
      @update:visible="editing = null"
    >
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">Nombre</label>
          <InputText v-model="editName" />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div class="flex flex-col gap-1">
            <label class="text-sm font-medium">Categoría</label>
            <Select
              v-model="editCategory"
              :options="categoryOptions"
              optionLabel="label"
              optionValue="value"
            />
          </div>
          <div class="flex flex-col gap-1">
            <label class="text-sm font-medium">Maleta de</label>
            <Select
              v-model="editTraveler"
              :options="bagMoveOptions"
              optionLabel="label"
              optionValue="value"
            />
          </div>
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">Enlace de compra</label>
          <InputText v-model="editUrl" placeholder="https://…" />
        </div>
      </div>
      <template #footer>
        <Button label="Cancelar" severity="secondary" text @click="editing = null" />
        <Button label="Guardar" @click="saveEdit" />
      </template>
    </Dialog>

    <!-- diálogo guardar plantilla nueva -->
    <Dialog
      v-model:visible="showSaveTemplate"
      modal
      header="Guardar como plantilla nueva"
      class="w-full max-w-md mx-4"
    >
      <p class="text-sm text-slate-500 mb-3">
        Se guardan los {{ activeItems.length }} elementos de la maleta de
        <strong>{{ activeBagLabel }}</strong> (sin marcar) como plantilla reutilizable.
      </p>
      <InputText
        v-model="templateName"
        placeholder="Nombre de la plantilla (p. ej. Playa, Montaña…)"
        class="w-full"
        @keyup.enter="saveTemplate"
      />
      <template #footer>
        <Button label="Cancelar" severity="secondary" text @click="showSaveTemplate = false" />
        <Button label="Guardar plantilla" icon="pi pi-save" @click="saveTemplate" />
      </template>
    </Dialog>
  </div>
</template>
