<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import Button from 'primevue/button'
import Select from 'primevue/select'
import ClusterBtn from '../../components/ui/ClusterBtn.vue'
import ExpenseFormDialog from '../../components/expenses/ExpenseFormDialog.vue'
import ExpenseImportDialog from '../../components/expenses/ExpenseImportDialog.vue'
import EmptyState from '../../components/EmptyState.vue'
import ExpenseStatsCards from '../../components/expenses/ExpenseStatsCards.vue'
import ExpenseFilterPanel from '../../components/expenses/ExpenseFilterPanel.vue'
import ExpenseBulkBar from '../../components/expenses/ExpenseBulkBar.vue'
import ExpenseTable from '../../components/expenses/ExpenseTable.vue'
import ExpenseList from '../../components/expenses/ExpenseList.vue'
import ExpenseChartsPanel from '../../components/expenses/ExpenseChartsPanel.vue'
import BalancesPanel from '../../components/expenses/BalancesPanel.vue'
import TabSkeleton from '../../components/TabSkeleton.vue'
import CollapsePanel from '../../components/ui/CollapsePanel.vue'
import FilterToggleButton from '../../components/ui/FilterToggleButton.vue'
import type { Expense, Trip } from '../../api/types'
import { useExpensesStore } from '../../stores/expenses'
import { useAttachmentsStore } from '../../stores/attachments'
import { useCategoriesStore } from '../../stores/categories'
import { usePlacesStore } from '../../stores/places'
import { useExpenseFilters } from '../../composables/useExpenseFilters'
import { useConfirmDelete } from '../../composables/useConfirmDelete'
import { useCrudView } from '../../composables/useCrudView'
import { useMediaQuery } from '../../composables/useMediaQuery'
import { useNotify } from '../../composables/useNotify'
import { useRafDeferred } from '../../composables/useRafDeferred'
import { useTripTabData } from '../../composables/useTripTabData'
import {
  budgetPercent,
  buildRows,
  computeStats,
  currencyBreakdown,
  groupTotals as computeGroupTotals,
  sortRows,
  tripDayCount,
  type ExpenseGroupBy,
  type ExpenseRow,
} from '../../utils/expenses'

const props = defineProps<{ trip: Trip }>()
const { t } = useI18n()
const store = useExpensesStore()
const attachments = useAttachmentsStore()
const categoriesStore = useCategoriesStore()
const places = usePlacesStore()
const confirmAction = useConfirmDelete()
const notify = useNotify()

function catColor(name: string): string {
  return categoriesStore.colorOf('expense', name)
}

const showImport = ref(false)

// bajo `sm` la tabla se sustituye por la lista apilada (sin scroll lateral)
const isDesktop = useMediaQuery('(min-width: 640px)')

const tableGroup = ref<ExpenseGroupBy>('none')
const tableGroupOptions = computed(() => [
  { value: 'none', label: t('expenses.group.none') },
  { value: 'day', label: t('expenses.group.byDay') },
  { value: 'category', label: t('expenses.group.byCategory') },
  { value: 'payer_name', label: t('expenses.group.byPayer') },
  { value: 'place_name', label: t('expenses.group.byPlace') },
])

const viewMode = ref<'table' | 'charts' | 'balances'>('table')
const viewOptions = computed(
  () =>
    [
      { value: 'table', label: t('expenses.view.table'), icon: 'pi pi-table' },
      { value: 'charts', label: t('expenses.view.charts'), icon: 'pi pi-chart-pie' },
      { value: 'balances', label: t('expenses.view.balances'), icon: 'pi pi-users' },
    ] as const,
)

// el cambio de vista se pinta en dos fases: primero el botón + skeleton (frame
// inmediato) y en el siguiente frame se monta la vista pesada — así el click
// responde al instante en vez de congelarse mientras renderiza la tabla
const { deferred: renderedView } = useRafDeferred(() => viewMode.value)

const route = useRoute()
// llegar desde una reserva/sitio/itinerario (?expense=id) enciende ese gasto
const highlightId = ref<number | null>(null)

useTripTabData(() => props.trip, {
  load(tripId) {
    store.load(tripId)
    categoriesStore.load('expense')
    places.load(tripId)
    attachments.load(tripId)
  },
  afterFirstLoad() {
    const fromQuery = Number(route.query.expense)
    if (fromQuery) {
      highlightId.value = fromQuery
      setTimeout(() => (highlightId.value = null), 4000)
    }
  },
})

const placeById = computed(() => new Map(places.items.map((p) => [p.id, p])))

// primer recibo de cada gasto → id del adjunto (enlace cruzado a Ficheros)
const receiptIds = computed(() => {
  const map = new Map<number, number>()
  for (const a of [...attachments.items].reverse()) {
    if (a.expense_id != null) map.set(a.expense_id, a.id)
  }
  return map
})

// primera carga (sin datos aún): skeleton en vez de métricas a cero
const initialLoading = computed(() => store.loading && !store.items.length)

const {
  filters,
  showFilters,
  filtered,
  activeFilterCount,
  clearFilters,
  memberById,
  placeNameOf,
  payerName,
  allCategoryNames,
  categoryFilterOptions,
  excludeOptions,
  placeFilterOptions,
} = useExpenseFilters({
  trip: () => props.trip,
  items: () => store.items,
  categoryNames: () => categoriesStore.expense.map((c) => c.name),
  placeById: () => placeById.value,
})

// ---- métricas ----
const stats = computed(() =>
  computeStats(
    filtered.value,
    props.trip.travelers.length,
    tripDayCount(props.trip.start_date, props.trip.end_date, filtered.value),
  ),
)
const breakdown = computed(() => currencyBreakdown(filtered.value, props.trip.base_currency))
const budgetPct = computed(() => budgetPercent(store.summary))

// ---- tabla ----
const rows = computed(() =>
  sortRows(buildRows(filtered.value, payerName, placeNameOf), tableGroup.value),
)
const groupTotals = computed(() => computeGroupTotals(rows.value, tableGroup.value))

// ---- selección múltiple y acciones en bloque ----
const selected = ref<ExpenseRow[]>([])
const bulkWorking = ref(false)

// la barra sigue montada mientras se recoge: conservar el último recuento
// evita que el rótulo cambie a "0 seleccionados" durante la animación
const bulkCount = ref(0)
watch(
  () => selected.value.length,
  (n) => {
    if (n) bulkCount.value = n
  },
)

const bulkCategoryOptions = computed(() =>
  allCategoryNames.value.map((name) => ({ value: name, label: name })),
)
function bulkPayerPayload(value: number | 'none' | 'common') {
  if (value === 'common') return { paid_by_common: true }
  if (value === 'none') return { paid_by_id: null, paid_by_common: false }
  return { paid_by_id: value }
}

async function applyBulk(payload: {
  category?: string
  paid_by_id?: number | null
  paid_by_common?: boolean
}) {
  bulkWorking.value = true
  try {
    const count = selected.value.length
    await store.bulkUpdate(selected.value.map((e) => e.id), payload)
    notify.success(t('expenses.toast.bulkUpdated', { n: count }))
    selected.value = []
  } finally {
    bulkWorking.value = false
  }
}

function bulkDelete() {
  const count = selected.value.length
  confirmAction({
    message: t('expenses.confirm.bulkDeleteMessage', { n: count }),
    header: t('expenses.confirm.bulkDeleteHeader'),
    acceptLabel: t('expenses.confirm.bulkDeleteAccept', { n: count }),
    accept: async () => {
      bulkWorking.value = true
      try {
        await store.bulkRemove(selected.value.map((e) => e.id))
        notify.success(t('expenses.toast.bulkDeleted', { n: count }))
        selected.value = []
      } finally {
        bulkWorking.value = false
      }
    },
  })
}

const {
  showForm,
  editing,
  openNew,
  openEdit,
  removeItem: removeExpense,
} = useCrudView<Expense>({
  confirm: (expense) => ({
    message: t('expenses.confirm.deleteMessage', { name: expense.description }),
    header: t('expenses.confirm.deleteHeader'),
  }),
  remove: (expense) => store.remove(expense.id),
})
</script>

<template>
  <div>
    <div v-if="initialLoading" class="flex flex-col gap-5">
      <TabSkeleton variant="stats" />
      <TabSkeleton variant="table" :rows="8" />
    </div>

    <template v-else>
    <ExpenseStatsCards
      :stats="stats"
      :summary="store.summary"
      :budgetPct="budgetPct"
      :currency="trip.base_currency"
      :activeFilterCount="activeFilterCount"
      :currencyBreakdown="breakdown"
    />

    <!-- barra de acciones -->
    <div class="flex flex-wrap items-center gap-2 mb-3">
      <Button :label="$t('expenses.actions.newExpense')" icon="pi pi-plus" class="w-full sm:w-auto" @click="openNew" />
      <FilterToggleButton
        v-if="viewMode !== 'balances'"
        v-model="showFilters"
        :count="activeFilterCount"
      />
      <Select
        v-if="viewMode === 'table'"
        v-model="tableGroup"
        :options="tableGroupOptions"
        optionLabel="label"
        optionValue="value"
        class="flex-1 sm:flex-none sm:w-52"
      />
      <!-- en móvil el panel salta aquí (justo bajo su botón); en desktop order-last lo baja
           tras la fila única. -mt-2 anula el gap extra de la línea fantasma cerrada -->
      <CollapsePanel
        v-if="viewMode !== 'balances'"
        :open="showFilters"
        class="w-full sm:order-last -mt-2"
      >
        <div class="pt-2">
          <ExpenseFilterPanel
            :filters="filters"
            :categoryOptions="categoryFilterOptions"
            :excludeOptions="excludeOptions"
            :travelers="trip.travelers"
            :placeOptions="placeFilterOptions"
            :activeFilterCount="activeFilterCount"
            @clear="clearFilters"
          />
        </div>
      </CollapsePanel>
      <span class="hidden sm:block flex-1" />
      <ClusterBtn v-model="viewMode" :options="viewOptions" class="flex-1 sm:flex-none" />
      <Button
        icon="pi pi-file-import"
        severity="secondary"
        outlined
        v-tooltip.bottom="$t('expenses.actions.importCsv')"
        @click="showImport = true"
      />
      <a :href="store.exportUrl()" download>
        <Button
          icon="pi pi-file-export"
          severity="secondary"
          outlined
          v-tooltip.bottom="$t('expenses.actions.exportCsv')"
        />
      </a>
    </div>

    <EmptyState
      v-if="!store.loading && !store.items.length"
      icon="pi pi-wallet"
      :title="$t('expenses.empty.title')"
      :subtitle="$t('expenses.empty.subtitle')"
    />

    <div v-else>
      <TabSkeleton
        v-if="renderedView !== viewMode"
        :variant="viewMode === 'table' ? 'table' : 'cards'"
        :rows="8"
      />
      <p
        v-else-if="renderedView !== 'balances' && !filtered.length"
        class="text-center text-sm text-ink-faint py-10"
      >
        {{ $t('expenses.empty.noMatch') }}
      </p>
      <div v-else-if="renderedView === 'table'" class="tt-anim-rise">
        <!-- la barra de acciones en bloque despliega y recoge como el panel de
             filtros: la tabla se desplaza con ella en vez de dar un salto -->
        <CollapsePanel :open="!!selected.length">
          <ExpenseBulkBar
            :count="bulkCount"
            :working="bulkWorking"
            :categoryOptions="bulkCategoryOptions"
            :travelers="trip.travelers"
            @set-category="(name) => applyBulk({ category: name })"
            @set-payer="(value) => applyBulk(bulkPayerPayload(value))"
            @delete="bulkDelete"
            @clear="selected = []"
          />
        </CollapsePanel>

        <component
          :is="isDesktop ? ExpenseTable : ExpenseList"
          v-model:selection="selected"
          :rows="rows"
          :groupBy="tableGroup"
          :groupTotals="groupTotals"
          :memberById="memberById"
          :placeById="placeById"
          :trip="trip"
          :catColor="catColor"
          :highlightId="highlightId"
          :receiptIds="receiptIds"
          @edit="openEdit"
          @remove="removeExpense"
        />
      </div>

      <div v-else-if="renderedView === 'charts'" class="tt-anim-rise">
        <ExpenseChartsPanel
          :filtered="filtered"
          :trip="trip"
          :catColor="catColor"
          :payerName="payerName"
          :placeNameOf="placeNameOf"
          :excludedCategories="filters.excludedCategories"
        />
      </div>

      <div v-else class="tt-anim-rise">
        <BalancesPanel :trip="trip" />
      </div>
    </div>
    </template>

    <ExpenseFormDialog v-model:visible="showForm" :trip="trip" :expense="editing" />
    <ExpenseImportDialog v-model:visible="showImport" :trip="trip" />
  </div>
</template>
