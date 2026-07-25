<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import Checkbox from 'primevue/checkbox'
import EmptyState from '../../components/EmptyState.vue'
import TabSkeleton from '../../components/TabSkeleton.vue'
import FormDialog from '../../components/ui/FormDialog.vue'
import ProgressMeter from '../../components/ui/ProgressMeter.vue'
import RowActions from '../../components/ui/RowActions.vue'
import BagSelector, { type BagOption } from '../../components/packing/BagSelector.vue'
import PackingAddBar from '../../components/packing/PackingAddBar.vue'
import PackingCategoryCard from '../../components/packing/PackingCategoryCard.vue'
import PackingItemDialog from '../../components/packing/PackingItemDialog.vue'
import type { PackingItem, Trip } from '../../api/types'
import { usePackingStore } from '../../stores/packing'
import { useCategoriesStore } from '../../stores/categories'
import { useConfirmDelete } from '../../composables/useConfirmDelete'
import { useNotify } from '../../composables/useNotify'
import { useTripTabData } from '../../composables/useTripTabData'
import { groupPackingItems } from '../../utils/packing'

const props = defineProps<{ trip: Trip }>()
const store = usePackingStore()
const categories = useCategoriesStore()
const confirmAction = useConfirmDelete()
const notify = useNotify()
const { t } = useI18n()

// maleta activa: null = común, número = viajero
const activeTraveler = ref<number | null>(null)
const selectedTemplate = ref<number | null>(null)

const editing = ref<PackingItem | null>(null)
const showEdit = ref(false)

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

function bagProgress(travelerId: number | null): { done: number; total: number } {
  const items = store.itemsFor(travelerId)
  return { done: items.filter((i) => i.checked).length, total: items.length }
}

const bags = computed<BagOption[]>(() =>
  [
    { travelerId: null as number | null, label: t('packing.commonBag'), color: null as string | null },
    ...props.trip.travelers.map((t) => ({ travelerId: t.id, label: t.name, color: t.color })),
  ].map((b) => ({ ...b, ...bagProgress(b.travelerId) })),
)

const activeItems = computed(() => store.itemsFor(activeTraveler.value))

const activeProgress = computed(() => {
  const { done, total } = bagProgress(activeTraveler.value)
  return { done, total, pct: total ? Math.round((done / total) * 100) : 0 }
})

const activeBagLabel = computed(
  () => bags.value.find((b) => b.travelerId === activeTraveler.value)?.label ?? t('packing.commonBag'),
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

async function addItem(payload: { name: string; category: string; url: string | null }) {
  try {
    await store.create({ ...payload, traveler_id: activeTraveler.value })
  } catch (err) {
    notify.error(t('packing.toast.addError'), err)
    throw err // PackingAddBar conserva el texto si falla
  }
}

function openEdit(item: PackingItem) {
  editing.value = item
  showEdit.value = true
}

function removeItem(item: PackingItem) {
  confirmAction({
    message: t('packing.confirmRemoveItem.message', { name: item.name }),
    header: t('packing.confirmRemoveItem.header'),
    accept: () => store.remove(item.id),
  })
}

async function applyTemplate() {
  if (selectedTemplate.value == null) return
  await store.applyTemplate(selectedTemplate.value, activeTraveler.value)
  notify.success(
    t('packing.toast.templateApplied', { bag: activeBagLabel.value }),
    t('packing.toast.templateAppliedDetail'),
  )
}

function syncTemplate() {
  if (selectedTemplate.value == null) return
  const template = store.templates.find((t) => t.id === selectedTemplate.value)
  confirmAction({
    message: t('packing.syncDialog.message', {
      name: template?.name,
      count: activeItems.value.length,
      bag: activeBagLabel.value,
    }),
    header: t('packing.syncDialog.header'),
    icon: 'pi pi-sync',
    acceptLabel: t('packing.syncDialog.accept'),
    acceptSeverity: undefined,
    accept: async () => {
      await store.syncTemplateFromTrip(selectedTemplate.value!, activeTraveler.value)
      notify.success(t('packing.toast.templateUpdated'))
    },
  })
}

async function saveTemplate() {
  const name = templateName.value.trim()
  if (!name) return
  try {
    await store.saveAsTemplate(name, activeTraveler.value)
    notify.success(t('packing.toast.templateSaved', { name }))
    showSaveTemplate.value = false
    templateName.value = ''
    syncSelectedTemplate()
  } catch (err) {
    notify.error(t('packing.toast.saveError'), err)
  }
}
</script>

<template>
  <div>
    <!-- selector de maleta: común + una por viajero -->
    <BagSelector v-model:active="activeTraveler" :bags="bags" class="mb-4">
      <p v-if="!trip.travelers.length" class="text-xs text-ink-faint sm:ml-2 max-sm:col-span-full self-center">
        {{ $t('packing.noTravelersHint') }}
      </p>
    </BagSelector>

    <!-- barra de la maleta activa: plantilla + progreso -->
    <div class="bg-surface rounded-card border border-line p-4 mb-4">
      <div class="flex flex-wrap items-center gap-2">
        <span class="text-sm font-semibold text-ink-secondary mr-1">
          {{ $t('packing.bagOf', { bag: activeBagLabel }) }}
        </span>
        <span v-if="activeTemplateName" class="text-xs px-2 py-0.5 rounded-full bg-info-tint text-info-strong">
          <i class="pi pi-briefcase text-3xs" /> {{ $t('packing.templateBadge', { name: activeTemplateName }) }}
        </span>
        <span class="flex-1" />
        <Select
          v-model="selectedTemplate"
          :options="templateOptions"
          optionLabel="label"
          optionValue="value"
          :placeholder="$t('packing.chooseTemplate')"
          class="w-full sm:w-52"
          size="small"
        />
        <Button
          v-if="selectedTemplate != null"
          :label="$t('packing.apply')"
          icon="pi pi-download"
          severity="secondary"
          size="small"
          v-tooltip.bottom="$t('packing.applyTooltip')"
          @click="applyTemplate"
        />
        <Button
          v-if="selectedTemplate != null && activeItems.length"
          icon="pi pi-sync"
          severity="secondary"
          outlined
          size="small"
          v-tooltip.bottom="$t('packing.syncTooltip')"
          @click="syncTemplate"
        />
        <Button
          v-if="activeItems.length"
          :label="$t('packing.newTemplate')"
          icon="pi pi-save"
          severity="secondary"
          outlined
          size="small"
          v-tooltip.bottom="$t('packing.newTemplateTooltip')"
          @click="showSaveTemplate = true"
        />
      </div>
      <div v-if="activeProgress.total" class="mt-3">
        <ProgressMeter :value="activeProgress.pct" />
        <p class="text-xs text-ink-faint mt-1">
          {{ $t('packing.progress', { done: activeProgress.done, total: activeProgress.total, pct: activeProgress.pct }) }}
        </p>
      </div>
    </div>

    <!-- añadir elemento a la maleta activa -->
    <PackingAddBar
      :placeholder="$t('packing.addToBagPlaceholder', { bag: activeBagLabel })"
      :categoryOptions="categoryOptions"
      :onAdd="addItem"
      class="mb-5"
    />

    <TabSkeleton v-if="store.loading && !store.items.length" variant="list" :rows="8" />

    <EmptyState
      v-else-if="!store.loading && !activeItems.length"
      icon="pi pi-briefcase"
      :title="$t('packing.empty.title', { bag: activeBagLabel })"
      :subtitle="$t('packing.empty.subtitle')"
    />

    <div v-else class="tt-stagger grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 items-start">
      <PackingCategoryCard
        v-for="group in grouped"
        :key="group.name"
        :name="group.name"
        :color="group.color"
        :count="`${group.items.filter((i) => i.checked).length}/${group.items.length}`"
      >
        <li
          v-for="item in group.items"
          :key="item.id"
          class="flex items-center gap-3 px-4 py-2 border-b border-line-faint last:border-b-0 hover:bg-surface-hover group/item"
        >
          <Checkbox :modelValue="item.checked" binary @update:modelValue="store.toggle(item)" />
          <span
            class="flex-1 transition-colors duration-200"
            :class="{ 'line-through text-ink-faint': item.checked }"
          >
            {{ item.name }}
            <a
              v-if="item.url"
              :href="item.url"
              target="_blank"
              rel="noopener"
              class="ml-1 text-info hover:underline text-xs"
              v-tooltip.top="$t('packing.purchaseLink')"
              @click.stop
            >
              <i class="pi pi-shopping-cart" />
            </a>
          </span>
          <RowActions @edit="openEdit(item)" @remove="removeItem(item)" />
        </li>
      </PackingCategoryCard>
    </div>

    <!-- diálogo editar (permite mover entre maletas) -->
    <PackingItemDialog
      v-model:visible="showEdit"
      :item="editing"
      :categoryOptions="categoryOptions"
      :bagOptions="bagMoveOptions"
    />

    <!-- diálogo guardar plantilla nueva -->
    <FormDialog
      v-model:visible="showSaveTemplate"
      :header="$t('packing.saveTemplateDialog.title')"
      width="md"
      @save="saveTemplate"
    >
      <i18n-t keypath="packing.saveTemplateDialog.body" tag="p" scope="global" class="text-sm text-ink-muted">
        <template #count>{{ activeItems.length }}</template>
        <template #bag><strong>{{ activeBagLabel }}</strong></template>
      </i18n-t>
      <InputText
        v-model="templateName"
        :placeholder="$t('packing.saveTemplateDialog.namePlaceholder')"
        class="w-full"
        @keyup.enter="saveTemplate"
      />
      <template #footer>
        <Button :label="$t('common.actions.cancel')" severity="secondary" text @click="showSaveTemplate = false" />
        <Button :label="$t('packing.saveTemplateDialog.save')" icon="pi pi-save" @click="saveTemplate" />
      </template>
    </FormDialog>
  </div>
</template>
