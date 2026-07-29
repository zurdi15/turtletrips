<script setup lang="ts">
import { ref } from 'vue'
import Checkbox from 'primevue/checkbox'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Tag from 'primevue/tag'
import PayerBadge from './PayerBadge.vue'
import RowActions from '../ui/RowActions.vue'
import EntityLink from '../trip/EntityLink.vue'
import ExpenseNote from './ExpenseNote.vue'
import type { Expense, Place, Traveler, Trip } from '../../api/types'
import {
  isGroupSelected,
  rowGroupKey,
  toggleGroupSelection,
  type ExpenseGroupBy,
  type ExpenseRow,
} from '../../utils/expenses'
import { formatDate, formatMoney } from '../../composables/useMoney'
import { useRowFlash } from '../../composables/useRowFlash'

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

// --- resaltar un gasto al llegar enlazado (?expense=id desde reserva/sitio/itinerario) ---

const tableRef = ref<{ $el?: HTMLElement } | null>(null)
const first = ref(0)
const pageRows = ref(50)

const { rowClass } = useRowFlash({
  rows: () => props.rows,
  highlightId: () => props.highlightId,
  first,
  pageRows,
  root: () => tableRef.value?.$el,
})
</script>

<template>
  <DataTable
    ref="tableRef"
    v-model:selection="selected"
    v-model:first="first"
    :value="rows"
    dataKey="id"
    size="small"
    stripedRows
    paginator
    :rows="50"
    :rowsPerPageOptions="[25, 50, 100, 200]"
    :alwaysShowPaginator="false"
    :rowClass="rowClass"
    @page="(e) => (pageRows = e.rows)"
    :tableStyle="{ minWidth: '640px' }"
    :rowGroupMode="groupBy !== 'none' ? 'subheader' : undefined"
    :groupRowsBy="groupBy !== 'none' ? groupBy : undefined"
    class="bg-surface rounded-card overflow-hidden border border-line"
    :class="{ 'tt-grouped': groupBy !== 'none' }"
  >
    <Column selectionMode="multiple" headerStyle="width: 2.5rem" />
    <template v-if="groupBy !== 'none'" #groupheader="{ data }">
      <div class="flex items-center gap-3 py-0.5">
        <Checkbox
          :modelValue="isGroupSelected(rows, selected, data, groupBy)"
          binary
          v-tooltip.right="$t('expenses.table.selectGroup')"
          @update:modelValue="selected = toggleGroupSelection(rows, selected, data, groupBy)"
          @click.stop
        />
        <span class="font-semibold text-ink">{{ groupLabel(data) }}</span>
        <span class="text-xs text-ink-faint">
          {{ $t('expenses.table.groupCount', { n: groupTotals.get(rowGroupKey(data, groupBy))?.count ?? 0 }) }}
        </span>
        <span class="ml-auto font-semibold text-ink">
          {{ formatMoney(groupTotals.get(rowGroupKey(data, groupBy))?.total ?? 0, trip.base_currency) }}
        </span>
      </div>
    </template>
    <Column :header="$t('expenses.fields.date')" field="day" style="width: 7rem">
      <template #body="{ data }">{{ formatDate(data.day) }}</template>
    </Column>
    <Column :header="$t('expenses.fields.category')" field="category" style="width: 9rem">
      <template #body="{ data }">
        <Tag
          :value="data.category"
          :style="{
            background: `${catColor(data.category)}20`,
            color: catColor(data.category),
          }"
        />
      </template>
    </Column>
    <Column :header="$t('expenses.fields.description')" field="description">
      <template #body="{ data }">
        <span>{{ data.description }}</span>
        <!-- reserva y sitio como iconos agrupados: fila propia en móvil
             (como en las tarjetas de reserva), en línea desde sm -->
        <span
          v-if="data.booking_id || (data.place_id && placeById.get(data.place_id)) || receiptIds?.has(data.id)"
          class="mt-1.5 flex items-center gap-2 sm:mt-0 sm:ml-2 sm:inline-flex sm:align-middle"
        >
          <EntityLink
            v-if="receiptIds?.has(data.id)"
            type="attachment"
            :tripId="trip.id"
            :targetId="receiptIds.get(data.id)!"
            :tooltip="$t('expenses.table.viewReceipt')"
          />
          <EntityLink v-if="data.booking_id" type="booking" :tripId="trip.id" :targetId="data.booking_id" />
          <EntityLink
            v-if="data.place_id && placeById.get(data.place_id)"
            type="place"
            :tripId="trip.id"
            :targetId="data.place_id"
            :tooltip="$t('expenses.table.placeTooltip', { name: placeById.get(data.place_id)!.name })"
          />
        </span>
        <ExpenseNote v-if="data.notes" :text="data.notes" />
      </template>
    </Column>
    <Column :header="$t('expenses.fields.amount')" style="width: 8rem">
      <template #body="{ data }">
        <div class="text-right">
          <div class="font-medium">{{ formatMoney(data.amount_base, trip.base_currency) }}</div>
          <div v-if="data.currency !== trip.base_currency" class="text-xs text-ink-faint">
            {{ formatMoney(data.amount, data.currency) }}
          </div>
        </div>
      </template>
    </Column>
    <Column :header="$t('expenses.table.paid')" field="payer_name" style="width: 7rem">
      <template #body="{ data }">
        <PayerBadge :expense="data" :memberById="memberById">
          <span class="text-ink-disabled text-xs">—</span>
        </PayerBadge>
      </template>
    </Column>
    <Column style="width: 5.5rem">
      <template #body="{ data }">
        <RowActions
          always
          class="justify-end"
          @edit="$emit('edit', data)"
          @remove="$emit('remove', data)"
        />
      </template>
    </Column>
  </DataTable>
</template>

<style scoped>
/* con agrupación, las filas de datos (no el header del grupo) se indentan
   para distinguir qué pertenece a cada agrupación */
.tt-grouped
  :deep(.p-datatable-tbody > tr:not(.p-datatable-row-group-header) > td:first-child) {
  padding-left: 1.75rem;
}

/* size="small" deja las filas muy apretadas: un poco más de aire vertical */
:deep(.p-datatable-tbody > tr:not(.p-datatable-row-group-header) > td) {
  padding-block: 0.625rem;
}

/* gasto enlazado desde otra pestaña: se enciende y se apaga suave al limpiar */
:deep(.p-datatable-tbody > tr > td) {
  transition: background-color var(--tt-dur-600) ease;
}
:deep(.p-datatable-tbody > tr.tt-row-flash > td) {
  background: color-mix(in srgb, var(--p-primary-color) 14%, transparent) !important;
}

/* el contenedor interno solo necesita scroll horizontal (el vertical es de la
   página): sin esto, las filas entrando desde +8px hacen aparecer un scrollbar
   vertical fugaz durante la animación. !important porque PrimeVue pone su
   overflow: auto como estilo inline (inlineStyles.tableContainer). */
:deep(.p-datatable-table-container) {
  overflow-y: hidden !important;
}

/* las filas entran en cascada rápida al montarse (o al cambiar de página);
   a partir de la 12ª entran juntas para no alargar la espera.
   reduced-motion lo cubre el guard global de style.css */
:deep(.p-datatable-tbody > tr) {
  animation: tt-rise-in var(--tt-dur-250) var(--tt-ease-spring) both;
}
:deep(.p-datatable-tbody > tr:nth-child(2)) {
  animation-delay: calc(var(--tt-stagger-step-dense) * 1);
}
:deep(.p-datatable-tbody > tr:nth-child(3)) {
  animation-delay: calc(var(--tt-stagger-step-dense) * 2);
}
:deep(.p-datatable-tbody > tr:nth-child(4)) {
  animation-delay: calc(var(--tt-stagger-step-dense) * 3);
}
:deep(.p-datatable-tbody > tr:nth-child(5)) {
  animation-delay: calc(var(--tt-stagger-step-dense) * 4);
}
:deep(.p-datatable-tbody > tr:nth-child(6)) {
  animation-delay: calc(var(--tt-stagger-step-dense) * 5);
}
:deep(.p-datatable-tbody > tr:nth-child(7)) {
  animation-delay: calc(var(--tt-stagger-step-dense) * 6);
}
:deep(.p-datatable-tbody > tr:nth-child(8)) {
  animation-delay: calc(var(--tt-stagger-step-dense) * 7);
}
:deep(.p-datatable-tbody > tr:nth-child(9)) {
  animation-delay: calc(var(--tt-stagger-step-dense) * 8);
}
:deep(.p-datatable-tbody > tr:nth-child(10)) {
  animation-delay: calc(var(--tt-stagger-step-dense) * 9);
}
:deep(.p-datatable-tbody > tr:nth-child(11)) {
  animation-delay: calc(var(--tt-stagger-step-dense) * 10);
}
:deep(.p-datatable-tbody > tr:nth-child(n + 12)) {
  animation-delay: calc(var(--tt-stagger-step-dense) * 11);
}
</style>
