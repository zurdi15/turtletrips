<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import Checkbox from 'primevue/checkbox'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Tag from 'primevue/tag'
import MemberChip from '../MemberChip.vue'
import Pill from '../ui/Pill.vue'
import RowActions from '../ui/RowActions.vue'
import EntityLink from '../trip/EntityLink.vue'
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
  highlightId?: number | null
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

// --- resaltar un gasto al llegar enlazado (?expense=id desde reserva/sitio/itinerario) ---

const tableRef = ref<{ $el?: HTMLElement } | null>(null)
const first = ref(0)
const pageRows = ref(50)
// las filas se recargan varias veces al montar: un solo scroll por gasto,
// o el smooth-scroll se reinicia a mitad y "bota"
let scrolledFor: number | null = null

function rowClass(data: ExpenseRow): string {
  return data.id === props.highlightId ? 'tt-row-flash' : ''
}

watch(
  [() => props.highlightId, () => props.rows],
  async () => {
    const id = props.highlightId
    if (id == null) {
      scrolledFor = null
      return
    }
    if (scrolledFor === id) return
    const idx = props.rows.findIndex((r) => r.id === id)
    if (idx < 0) return
    scrolledFor = id
    // saltar a la página donde vive el gasto y centrarlo
    first.value = Math.floor(idx / pageRows.value) * pageRows.value
    await nextTick()
    tableRef.value?.$el
      ?.querySelector('.tt-row-flash')
      ?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  },
  { immediate: true },
)
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
        <!-- reserva y sitio como iconos agrupados (saltan de línea juntos) -->
        <span
          v-if="data.booking_id || (data.place_id && placeById.get(data.place_id))"
          class="inline-flex items-center gap-2 ml-2 align-middle"
        >
          <EntityLink v-if="data.booking_id" type="booking" :tripId="trip.id" :targetId="data.booking_id" />
          <EntityLink
            v-if="data.place_id && placeById.get(data.place_id)"
            type="place"
            :tripId="trip.id"
            :targetId="data.place_id"
            :tooltip="`Sitio: ${placeById.get(data.place_id)!.name}`"
          />
        </span>
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
        <Pill
          v-if="data.paid_by_common"
          color="warn"
          icon="pi pi-wallet"
          v-tooltip.top="'Pagado del fondo común: no entra en los saldos'"
        >
          Común
        </Pill>
        <MemberChip
          v-else-if="data.paid_by_id != null && memberById.get(data.paid_by_id)"
          :member="memberById.get(data.paid_by_id)!"
        />
        <span v-else class="text-slate-300 text-xs">—</span>
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
