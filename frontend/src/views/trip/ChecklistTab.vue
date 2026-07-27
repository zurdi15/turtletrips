<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Checkbox from 'primevue/checkbox'
import DatePicker from 'primevue/datepicker'
import InputText from 'primevue/inputtext'
import EmptyState from '../../components/EmptyState.vue'
import TabSkeleton from '../../components/TabSkeleton.vue'
import ProgressMeter from '../../components/ui/ProgressMeter.vue'
import RowActions from '../../components/ui/RowActions.vue'
import ChecklistItemDialog from '../../components/checklist/ChecklistItemDialog.vue'
import type { ChecklistItem, Trip } from '../../api/types'
import { useChecklistStore } from '../../stores/checklist'
import { useCrudView } from '../../composables/useCrudView'
import { useNotify } from '../../composables/useNotify'
import { useTripTabData } from '../../composables/useTripTabData'
import { formatDate, toIsoDate } from '../../composables/useMoney'
import { isOverdue, sortChecklist } from '../../utils/checklist'

const props = defineProps<{ trip: Trip }>()
const { t } = useI18n()
const store = useChecklistStore()
const notify = useNotify()

useTripTabData(() => props.trip, {
  load(tripId) {
    store.load(tripId)
  },
})

const initialLoading = computed(() => store.loading && !store.items.length)
const sorted = computed(() => sortChecklist(store.items))
const doneCount = computed(() => store.items.filter((i) => i.done).length)
const progressPct = computed(() =>
  store.items.length ? Math.round((doneCount.value / store.items.length) * 100) : 0,
)
const todayIso = toIsoDate(new Date())

// ---- alta rápida (título + fecha límite opcional) ----

const newTitle = ref('')
const newDue = ref<Date | null>(null)
const adding = ref(false)

async function add() {
  const title = newTitle.value.trim()
  if (!title) return
  adding.value = true
  try {
    await store.create({ title, due_date: newDue.value ? toIsoDate(newDue.value) : null })
    newTitle.value = ''
    newDue.value = null
  } catch (err) {
    notify.error(t('checklist.toast.addError'), err)
  } finally {
    adding.value = false
  }
}

async function toggle(item: ChecklistItem) {
  try {
    await store.update(item.id, { done: !item.done })
  } catch (err) {
    notify.error(t('common.form.saveError'), err)
  }
}

const { showForm, editing, openEdit, removeItem } = useCrudView<ChecklistItem>({
  confirm: (item) => ({
    message: t('checklist.confirm.message', { name: item.title }),
    header: t('checklist.confirm.header'),
  }),
  remove: (item) => store.remove(item.id),
})
</script>

<template>
  <div>
    <TabSkeleton v-if="initialLoading" variant="table" :rows="4" />

    <template v-else>
      <div class="flex flex-wrap items-center gap-2 mb-4">
        <InputText
          v-model="newTitle"
          :placeholder="t('checklist.addPlaceholder')"
          class="w-full sm:flex-1"
          @keyup.enter="add"
        />
        <DatePicker
          v-model="newDue"
          showIcon
          showButtonBar
          dateFormat="dd/mm/yy"
          :placeholder="t('checklist.duePlaceholder')"
          class="flex-1 sm:flex-none sm:w-44"
        />
        <Button
          :label="$t('common.actions.add')"
          icon="pi pi-plus"
          :loading="adding"
          class="max-sm:[&_.p-button-label]:hidden"
          @click="add"
        />
      </div>

      <div v-if="store.items.length" class="mb-4">
        <ProgressMeter :value="progressPct" />
        <p class="text-xs text-ink-faint mt-1">
          {{ t('checklist.progress', { done: doneCount, total: store.items.length }) }}
        </p>
      </div>

      <EmptyState
        v-if="!store.items.length"
        icon="pi pi-check-square"
        :title="t('checklist.empty.title')"
        :subtitle="t('checklist.empty.subtitle')"
      />

      <div
        v-else
        class="tt-stagger bg-surface rounded-card border border-line overflow-hidden divide-y divide-line-subtle"
      >
        <div
          v-for="item in sorted"
          :key="item.id"
          class="flex items-center gap-3 px-4 py-2.5 group/item hover:bg-surface-hover"
        >
          <Checkbox :modelValue="item.done" binary @update:modelValue="toggle(item)" />
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 flex-wrap">
              <span
                class="text-sm font-medium transition-colors duration-200"
                :class="item.done ? 'line-through text-ink-faint' : 'text-ink'"
              >
                {{ item.title }}
              </span>
              <span
                v-if="item.due_date"
                class="inline-flex items-center gap-1 text-xs whitespace-nowrap"
                :class="isOverdue(item, todayIso) ? 'text-red-600 font-medium' : 'text-ink-faint'"
              >
                <i class="pi pi-calendar text-2xs" />
                {{ formatDate(item.due_date) }}
              </span>
              <a
                v-if="item.url"
                :href="item.url"
                target="_blank"
                rel="noopener"
                class="text-info hover:underline text-xs"
                v-tooltip.top="$t('checklist.linkTooltip')"
                @click.stop
              >
                <i class="pi pi-external-link" />
              </a>
            </div>
            <p v-if="item.notes" class="text-xs text-ink-faint mt-0.5">{{ item.notes }}</p>
          </div>
          <RowActions class="justify-end" @edit="openEdit(item)" @remove="removeItem(item)" />
        </div>
      </div>
    </template>

    <ChecklistItemDialog v-model:visible="showForm" :item="editing" />
  </div>
</template>
