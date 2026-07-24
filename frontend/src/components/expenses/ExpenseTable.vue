<script setup lang="ts">
import Button from 'primevue/button'
import Checkbox from 'primevue/checkbox'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Tag from 'primevue/tag'
import MemberChip from '../MemberChip.vue'
import type { Expense, Place, Traveler, Trip } from '../../api/types'
import type { ExpenseGroupBy, ExpenseRow } from '../../utils/expenses'
import { formatDate, formatMoney } from '../../composables/useMoney'

const props = defineProps<{
  rows: ExpenseRow[]
  groupBy: ExpenseGroupBy
  groupTotals: Map<string, { total: number; count: number }>
  memberById: Map<number, Traveler>
  placeById: Map<number, Place>
  trip: Trip
  catColor: (name: string) => string
}>()

defineEmits<{ edit: [expense: Expense]; remove: [expense: Expense] }>()

const selected = defineModel<ExpenseRow[]>('selection', { required: true })

function groupLabel(row: ExpenseRow): string {
  if (props.groupBy === 'day') return formatDate(row.day)
  if (props.groupBy === 'category') return row.category
  if (props.groupBy === 'place_name') return row.place_name
  return row.payer_name
}
function groupKey(row: ExpenseRow): string {
  return String(row[props.groupBy as keyof ExpenseRow])
}

// --- selección por grupo (todos los gastos de un día/pagador/categoría/sitio) ---

function groupRows(row: ExpenseRow): ExpenseRow[] {
  return props.rows.filter((r) => groupKey(r) === groupKey(row))
}

function isGroupSelected(row: ExpenseRow): boolean {
  const rows = groupRows(row)
  return rows.length > 0 && rows.every((r) => selected.value.some((s) => s.id === r.id))
}

function toggleGroup(row: ExpenseRow) {
  const rows = groupRows(row)
  if (isGroupSelected(row)) {
    const ids = new Set(rows.map((r) => r.id))
    selected.value = selected.value.filter((s) => !ids.has(s.id))
  } else {
    const have = new Set(selected.value.map((s) => s.id))
    selected.value = [...selected.value, ...rows.filter((r) => !have.has(r.id))]
  }
}
</script>

<template>
  <DataTable
    v-model:selection="selected"
    :value="rows"
    dataKey="id"
    size="small"
    stripedRows
    paginator
    :rows="50"
    :rowsPerPageOptions="[25, 50, 100, 200]"
    :alwaysShowPaginator="false"
    :tableStyle="{ minWidth: '640px' }"
    :rowGroupMode="groupBy !== 'none' ? 'subheader' : undefined"
    :groupRowsBy="groupBy !== 'none' ? groupBy : undefined"
    class="bg-white rounded-xl overflow-hidden border border-slate-200"
    :class="{ 'tt-grouped': groupBy !== 'none' }"
  >
    <Column selectionMode="multiple" headerStyle="width: 2.5rem" />
    <template v-if="groupBy !== 'none'" #groupheader="{ data }">
      <div class="flex items-center gap-3 py-0.5">
        <Checkbox
          :modelValue="isGroupSelected(data)"
          binary
          v-tooltip.right="'Seleccionar todo el grupo'"
          @update:modelValue="toggleGroup(data)"
          @click.stop
        />
        <span class="font-semibold text-slate-700">{{ groupLabel(data) }}</span>
        <span class="text-xs text-slate-400">
          {{ groupTotals.get(groupKey(data))?.count }} gastos
        </span>
        <span class="ml-auto font-semibold text-slate-700">
          {{ formatMoney(groupTotals.get(groupKey(data))?.total ?? 0, trip.base_currency) }}
        </span>
      </div>
    </template>
    <Column header="Fecha" field="day" style="width: 7rem">
      <template #body="{ data }">{{ formatDate(data.day) }}</template>
    </Column>
    <Column header="Categoría" field="category" style="width: 9rem">
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
    <Column header="Descripción" field="description">
      <template #body="{ data }">
        <span>{{ data.description }}</span>
        <router-link
          v-if="data.booking_id"
          :to="{ name: 'trip-bookings', params: { id: trip.id }, query: { booking: data.booking_id } }"
          class="ml-2 text-slate-400 hover:text-sky-600 no-underline"
          v-tooltip.top="'Ver reserva'"
        >
          <i class="pi pi-ticket text-xs" />
        </router-link>
        <router-link
          v-if="data.place_id && placeById.get(data.place_id)"
          :to="{ name: 'trip-places', params: { id: trip.id }, query: { place: data.place_id } }"
          class="mt-1.5 flex items-center gap-0.5 w-fit whitespace-nowrap text-xs text-emerald-600 hover:underline no-underline"
          v-tooltip.top="'Ver sitio'"
        >
          <i class="pi pi-map-marker text-[10px] no-underline" />
          <span>{{ placeById.get(data.place_id)!.name }}</span>
        </router-link>
        <p v-if="data.notes" class="mt-1.5 text-xs text-slate-400 truncate max-w-[16rem]">
          {{ data.notes }}
        </p>
      </template>
    </Column>
    <Column header="Importe" style="width: 8rem">
      <template #body="{ data }">
        <div class="text-right">
          <div class="font-medium">{{ formatMoney(data.amount_base, trip.base_currency) }}</div>
          <div v-if="data.currency !== trip.base_currency" class="text-xs text-slate-400">
            {{ formatMoney(data.amount, data.currency) }}
          </div>
        </div>
      </template>
    </Column>
    <Column header="Pagó" field="payer_name" style="width: 7rem">
      <template #body="{ data }">
        <span
          v-if="data.paid_by_common"
          class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-amber-50 text-amber-700"
          v-tooltip.top="'Pagado del fondo común: no entra en los saldos'"
        >
          <i class="pi pi-wallet text-[10px]" />
          Común
        </span>
        <MemberChip
          v-else-if="data.paid_by_id != null && memberById.get(data.paid_by_id)"
          :member="memberById.get(data.paid_by_id)!"
        />
        <span v-else class="text-slate-300 text-xs">—</span>
      </template>
    </Column>
    <Column style="width: 5.5rem">
      <template #body="{ data }">
        <div class="flex gap-1 justify-end">
          <Button
            icon="pi pi-pencil"
            text
            size="small"
            severity="secondary"
            @click="$emit('edit', data)"
          />
          <Button
            icon="pi pi-trash"
            text
            size="small"
            severity="danger"
            @click="$emit('remove', data)"
          />
        </div>
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

/* el contenedor interno solo necesita scroll horizontal (el vertical es de la
   página): sin esto, las filas entrando desde +8px hacen aparecer un scrollbar
   vertical fugaz durante la animación. !important porque PrimeVue pone su
   overflow: auto como estilo inline (inlineStyles.tableContainer). */
:deep(.p-datatable-table-container) {
  overflow-y: hidden !important;
}

/* las filas entran en cascada rápida al montarse (o al cambiar de página);
   a partir de la 12ª entran juntas para no alargar la espera */
:deep(.p-datatable-tbody > tr) {
  animation: tt-rise-in 0.25s cubic-bezier(0.22, 1, 0.36, 1) both;
}
:deep(.p-datatable-tbody > tr:nth-child(2)) {
  animation-delay: 25ms;
}
:deep(.p-datatable-tbody > tr:nth-child(3)) {
  animation-delay: 50ms;
}
:deep(.p-datatable-tbody > tr:nth-child(4)) {
  animation-delay: 75ms;
}
:deep(.p-datatable-tbody > tr:nth-child(5)) {
  animation-delay: 100ms;
}
:deep(.p-datatable-tbody > tr:nth-child(6)) {
  animation-delay: 125ms;
}
:deep(.p-datatable-tbody > tr:nth-child(7)) {
  animation-delay: 150ms;
}
:deep(.p-datatable-tbody > tr:nth-child(8)) {
  animation-delay: 175ms;
}
:deep(.p-datatable-tbody > tr:nth-child(9)) {
  animation-delay: 200ms;
}
:deep(.p-datatable-tbody > tr:nth-child(10)) {
  animation-delay: 225ms;
}
:deep(.p-datatable-tbody > tr:nth-child(11)) {
  animation-delay: 250ms;
}
:deep(.p-datatable-tbody > tr:nth-child(n + 12)) {
  animation-delay: 275ms;
}
@media (prefers-reduced-motion: reduce) {
  :deep(.p-datatable-tbody > tr) {
    animation: none;
  }
}
</style>
