<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import Checkbox from 'primevue/checkbox'
import Paginator from 'primevue/paginator'
import Tag from 'primevue/tag'
import PayerBadge from './PayerBadge.vue'
import RowActions from '../ui/RowActions.vue'
import EntityLink from '../trip/EntityLink.vue'
import type { Expense, Place, Traveler, Trip } from '../../api/types'
import {
  isGroupSelected,
  rowGroupKey,
  toggleGroupSelection,
  toggleRowSelection,
  type ExpenseGroupBy,
  type ExpenseRow,
} from '../../utils/expenses'
import { formatDate, formatMoney } from '../../composables/useMoney'
import { useRowFlash } from '../../composables/useRowFlash'

// Variante móvil de ExpenseTable: filas apiladas a todo el ancho (sin scroll
// lateral), con la misma API — selección, grupos, resaltado y edición.
const props = defineProps<{
  rows: ExpenseRow[]
  groupBy: ExpenseGroupBy
  groupTotals: Map<string, { total: number; count: number }>
  memberById: Map<number, Traveler>
  placeById: Map<number, Place>
  trip: Trip
  catColor: (name: string) => string
  highlightId?: number | null
  /** primer recibo de cada gasto: paperclip que lleva a Ficheros con highlight */
  receiptIds?: Map<number, number>
}>()

defineEmits<{ edit: [expense: Expense]; remove: [expense: Expense] }>()

const selected = defineModel<ExpenseRow[]>('selection', { required: true })

function groupLabel(row: ExpenseRow): string {
  if (props.groupBy === 'day') return formatDate(row.day)
  if (props.groupBy === 'category') return row.category
  if (props.groupBy === 'place_name') return row.place_name
  return row.payer_name
}

function isRowSelected(row: ExpenseRow): boolean {
  return selected.value.some((s) => s.id === row.id)
}

// ---- paginación (misma página de 50 que la tabla, pager compacto) ----

const first = ref(0)
const pageRows = ref(50)

const paged = computed(() => props.rows.slice(first.value, first.value + pageRows.value))

// cabecera de grupo delante de la primera fila de cada grupo de la página
const rendered = computed(() =>
  paged.value.map((row, i) => ({
    row,
    header:
      props.groupBy !== 'none' &&
      (i === 0 || rowGroupKey(paged.value[i - 1], props.groupBy) !== rowGroupKey(row, props.groupBy)),
  })),
)

// al filtrar puede desaparecer la página actual: volver a la primera
watch(
  () => props.rows.length,
  (n) => {
    if (first.value >= n) first.value = 0
  },
)

// ---- resaltar un gasto al llegar enlazado (?expense=id) ----

const rootEl = ref<HTMLElement | null>(null)
const { rowClass } = useRowFlash({
  rows: () => props.rows,
  highlightId: () => props.highlightId,
  first,
  pageRows,
  root: () => rootEl.value,
})
</script>

<template>
  <div ref="rootEl" class="bg-surface rounded-card overflow-hidden border border-line">
    <div class="tt-stagger divide-y divide-line-subtle">
      <template v-for="entry in rendered" :key="entry.row.id">
        <!-- cabecera de grupo: checkbox de grupo + etiqueta + contador + total -->
        <div
          v-if="entry.header"
          class="flex items-center gap-2.5 px-3 py-2 bg-surface-muted"
        >
          <Checkbox
            :modelValue="isGroupSelected(rows, selected, entry.row, groupBy)"
            binary
            @update:modelValue="selected = toggleGroupSelection(rows, selected, entry.row, groupBy)"
          />
          <span class="font-semibold text-sm text-ink truncate">{{ groupLabel(entry.row) }}</span>
          <span class="text-xs text-ink-faint shrink-0">
            {{ $t('expenses.table.groupCount', { n: groupTotals.get(rowGroupKey(entry.row, groupBy))?.count ?? 0 }) }}
          </span>
          <span class="ml-auto font-semibold text-sm text-ink whitespace-nowrap">
            {{ formatMoney(groupTotals.get(rowGroupKey(entry.row, groupBy))?.total ?? 0, trip.base_currency) }}
          </span>
        </div>

        <div
          class="tt-list-row grid grid-cols-[auto_minmax(0,1fr)_auto] gap-x-2.5 px-3 py-2.5"
          :class="[rowClass(entry.row), { 'tt-row-selected': isRowSelected(entry.row) }]"
        >
          <Checkbox
            class="self-start mt-0.5"
            :modelValue="isRowSelected(entry.row)"
            binary
            @update:modelValue="selected = toggleRowSelection(selected, entry.row)"
          />

          <!-- izquierda: título, fecha y categoría -->
          <div class="min-w-0">
            <div class="flex items-center gap-2 min-w-0">
              <span class="text-sm text-ink break-words min-w-0">{{ entry.row.description }}</span>
              <EntityLink
                v-if="receiptIds?.has(entry.row.id)"
                type="attachment"
                :tripId="trip.id"
                :targetId="receiptIds.get(entry.row.id)!"
                :tooltip="$t('expenses.table.viewReceipt')"
              />
              <EntityLink
                v-if="entry.row.booking_id"
                type="booking"
                :tripId="trip.id"
                :targetId="entry.row.booking_id"
              />
              <EntityLink
                v-if="entry.row.place_id && placeById.get(entry.row.place_id)"
                type="place"
                :tripId="trip.id"
                :targetId="entry.row.place_id"
                :tooltip="$t('expenses.table.placeTooltip', { name: placeById.get(entry.row.place_id)!.name })"
              />
            </div>
            <!-- cada dato en su propia línea: se lee de arriba abajo sin mezclas -->
            <p class="mt-1 text-xs text-ink-faint">{{ formatDate(entry.row.day) }}</p>
            <div class="mt-1">
              <Tag
                :value="entry.row.category"
                :style="{
                  background: `${catColor(entry.row.category)}20`,
                  color: catColor(entry.row.category),
                }"
              />
            </div>
          </div>

          <!-- derecha: importe arriba (a la altura del título), pagador debajo
               y las acciones al pie de la fila -->
          <div class="flex flex-col items-end gap-1.5">
            <div class="text-right">
              <div class="text-sm font-medium text-ink whitespace-nowrap">
                {{ formatMoney(entry.row.amount_base, trip.base_currency) }}
              </div>
              <div
                v-if="entry.row.currency !== trip.base_currency"
                class="text-xs text-ink-faint whitespace-nowrap"
              >
                {{ formatMoney(entry.row.amount, entry.row.currency) }}
              </div>
            </div>
            <PayerBadge :expense="entry.row" :memberById="memberById" />
            <RowActions
              always
              class="mt-auto -mr-1.5 -mb-1"
              @edit="$emit('edit', entry.row)"
              @remove="$emit('remove', entry.row)"
            />
          </div>

          <!-- la nota, a lo ancho de la fila entera: en la columna estrecha se
               agolpaba en un churro de líneas cortas -->
          <p
            v-if="entry.row.notes"
            class="col-span-3 mt-2 text-xs text-ink-faint break-words"
          >
            {{ entry.row.notes }}
          </p>
        </div>
      </template>
    </div>

    <Paginator
      v-if="rows.length > pageRows"
      v-model:first="first"
      :rows="pageRows"
      :totalRecords="rows.length"
      template="PrevPageLink CurrentPageReport NextPageLink"
      currentPageReportTemplate="{currentPage} / {totalPages}"
      class="border-t border-line"
    />
  </div>
</template>

<style scoped>
/* gasto enlazado desde otra pestaña: se enciende y se apaga suave al limpiar */
.tt-list-row {
  transition: background-color var(--tt-dur-600) ease;
}
.tt-list-row.tt-row-selected {
  background: color-mix(in srgb, var(--p-primary-color) 8%, transparent);
}
.tt-list-row.tt-row-flash {
  background: color-mix(in srgb, var(--p-primary-color) 14%, transparent);
}
</style>
