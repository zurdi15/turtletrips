import { computed, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import type { Expense, Place, Trip } from '../api/types'
import {
  countActiveFilters,
  emptyFilters,
  filterExpenses,
  type ExpenseFilterState,
} from '../utils/expenses'

/**
 * Estado reactivo de los filtros de gastos + lookups de nombres y opciones
 * para los selectores. La lógica pura vive en utils/expenses.ts.
 */
export function useExpenseFilters(ctx: {
  trip: () => Trip
  items: () => Expense[]
  categoryNames: () => string[]
  placeById: () => Map<number, Place>
}) {
  const { t } = useI18n()
  const filters = reactive<ExpenseFilterState>(emptyFilters())
  const showFilters = ref(false)

  const memberById = computed(() => new Map(ctx.trip().travelers.map((t) => [t.id, t])))

  function placeNameOf(e: Expense): string {
    return e.place_id != null
      ? (ctx.placeById().get(e.place_id)?.name ?? t('expenses.noPlace'))
      : t('expenses.noPlace')
  }

  function payerName(e: Expense): string {
    if (e.paid_by_common) return t('expenses.payer.commonFund')
    return e.paid_by_id != null
      ? (memberById.value.get(e.paid_by_id)?.name ?? t('expenses.payer.unassigned'))
      : t('expenses.payer.unassigned')
  }

  const allCategoryNames = computed(() => {
    const names = new Set(ctx.categoryNames())
    for (const e of ctx.items()) names.add(e.category)
    return [...names]
  })

  const categoryFilterOptions = computed(() => [
    { value: 'all', label: t('expenses.filters.allCategories') },
    ...allCategoryNames.value.map((name) => ({ value: name, label: name })),
  ])
  const excludeOptions = computed(() =>
    allCategoryNames.value.map((name) => ({ value: name, label: name })),
  )
  const payerFilterOptions = computed(() => [
    { value: 'all' as const, label: t('expenses.filters.allPayers') },
    ...ctx.trip().travelers.map((t) => ({ value: t.id, label: t.name, color: t.color })),
    { value: 'common' as const, label: t('expenses.payer.commonFund') },
    { value: 'none' as const, label: t('expenses.payer.unassigned') },
  ])
  const placeFilterOptions = computed(() => {
    const usedIds = new Set(
      ctx.items().map((e) => e.place_id).filter((id): id is number => id != null),
    )
    return [
      { value: 'all' as const, label: t('expenses.filters.allPlaces') },
      ...[...usedIds]
        .map((id) => ({ value: id, label: ctx.placeById().get(id)?.name ?? `#${id}` }))
        .sort((a, b) => a.label.localeCompare(b.label, 'es')),
      { value: 'none' as const, label: t('expenses.noPlace') },
    ]
  })

  const activeFilterCount = computed(() => countActiveFilters(filters))

  function clearFilters() {
    Object.assign(filters, emptyFilters())
  }

  const filtered = computed(() => filterExpenses(ctx.items(), filters, placeNameOf))

  return {
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
    payerFilterOptions,
    placeFilterOptions,
  }
}
