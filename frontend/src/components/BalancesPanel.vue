<script setup lang="ts">
import { computed, onMounted, ref, watch, TransitionGroup } from 'vue'
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Message from 'primevue/message'
import { useToast } from 'primevue/usetoast'
import MemberChip from './MemberChip.vue'
import type { SettlementTransfer, Trip } from '../api/types'
import { useExpensesStore } from '../stores/expenses'
import { useTripsStore } from '../stores/trips'
import { formatDate, formatMoney } from '../composables/useMoney'

const props = defineProps<{ trip: Trip }>()
const store = useExpensesStore()
const trips = useTripsStore()
const toast = useToast()

onMounted(() => store.loadBalances())
watch(() => props.trip.id, () => store.loadBalances())

const data = computed(() => store.balances)
const money = (v: number) => formatMoney(v, props.trip.base_currency)

const settling = ref(false)

async function settle(transfer: SettlementTransfer) {
  settling.value = true
  try {
    await store.settle({
      from_id: transfer.from_id,
      to_id: transfer.to_id,
      amount_base: transfer.amount_base,
    })
    toast.add({
      severity: 'success',
      summary: `Pago registrado: ${transfer.from_name} → ${transfer.to_name}`,
      life: 3000,
    })
    // refresca la pill de "deudas saldadas" del viaje
    await trips.loadTrip(props.trip.id)
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: String(err), life: 4000 })
  } finally {
    settling.value = false
  }
}

async function undo(settlementId: number) {
  settling.value = true
  try {
    await store.unsettle(settlementId)
    await trips.loadTrip(props.trip.id)
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: String(err), life: 4000 })
  } finally {
    settling.value = false
  }
}
</script>

<template>
  <div v-if="data" class="flex flex-col gap-4">
    <Message v-if="data.unassigned_count > 0" severity="warn" size="small">
      {{ data.unassigned_count }}
      {{ data.unassigned_count === 1 ? 'gasto sin pagador' : 'gastos sin pagador' }}
      ({{ money(data.unassigned_total_base) }}) no se incluyen en los saldos.
    </Message>
    <p v-if="data.common_count > 0" class="text-xs text-slate-400 flex items-center gap-1.5">
      <i class="pi pi-wallet" />
      {{ data.common_count }}
      {{ data.common_count === 1 ? 'gasto pagado' : 'gastos pagados' }} del fondo común
      ({{ money(data.common_total_base) }}): cuentan en los totales pero no generan deudas.
    </p>

    <p v-if="!data.balances.length" class="text-center text-sm text-slate-400 py-10">
      Añade viajeros al viaje y asigna pagadores a los gastos para ver los saldos.
    </p>

    <template v-else>
      <DataTable
        :value="data.balances"
        dataKey="traveler_id"
        size="small"
        class="bg-white rounded-xl overflow-hidden border border-slate-200"
      >
        <Column header="Viajero">
          <template #body="{ data: b }">
            <MemberChip
              :member="{ id: b.traveler_id, name: b.name, color: b.color }"
            />
          </template>
        </Column>
        <Column header="Ha pagado">
          <template #body="{ data: b }">
            <span class="tabular-nums">{{ money(b.paid_base) }}</span>
          </template>
        </Column>
        <Column header="Le corresponde">
          <template #body="{ data: b }">
            <span class="tabular-nums">{{ money(b.owed_base) }}</span>
          </template>
        </Column>
        <Column header="Saldo">
          <template #body="{ data: b }">
            <span
              class="font-semibold tabular-nums"
              :class="
                b.net_base > 0 ? 'text-emerald-600' : b.net_base < 0 ? 'text-red-600' : 'text-slate-400'
              "
            >
              {{ b.net_base > 0 ? '+' : '' }}{{ money(b.net_base) }}
            </span>
          </template>
        </Column>
      </DataTable>

      <div
        v-if="data.debts_settled"
        class="tt-pop-in rounded-xl border border-emerald-200 bg-emerald-50 p-4 flex items-center gap-2 text-emerald-700 font-medium"
      >
        <i class="pi pi-check-circle" />
        Deudas saldadas
      </div>

      <div v-else class="bg-white rounded-xl border border-slate-200 p-4">
        <h3 class="text-sm font-semibold text-slate-700 mb-3">Liquidación sugerida</h3>
        <p v-if="!data.settlements.length" class="text-sm text-slate-400 flex items-center gap-1.5">
          <i class="pi pi-check-circle text-emerald-500" /> Todo cuadra: nadie debe nada.
        </p>
        <TransitionGroup v-else tag="ul" name="tt-list" class="relative flex flex-col gap-2">
          <li
            v-for="t in data.settlements"
            :key="`${t.from_id}-${t.to_id}`"
            class="flex items-center gap-2 text-sm text-slate-700"
          >
            <span class="font-medium">{{ t.from_name }}</span>
            <i class="pi pi-arrow-right text-xs text-slate-400" />
            <span class="font-medium">{{ t.to_name }}</span>
            <span class="ml-auto font-semibold tabular-nums">{{ money(t.amount_base) }}</span>
            <Button
              label="Liquidar"
              icon="pi pi-check"
              size="small"
              outlined
              :loading="settling"
              v-tooltip.left="'Marcar este pago como hecho'"
              @click="settle(t)"
            />
          </li>
        </TransitionGroup>
      </div>

      <div v-if="data.paid_settlements.length" class="bg-white rounded-xl border border-slate-200 p-4">
        <h3 class="text-sm font-semibold text-slate-700 mb-3">Pagos registrados</h3>
        <TransitionGroup tag="ul" name="tt-list" class="relative flex flex-col gap-2">
          <li
            v-for="s in data.paid_settlements"
            :key="s.id"
            class="flex items-center gap-2 text-sm text-slate-600"
          >
            <i class="pi pi-check-circle text-emerald-500 text-xs" />
            <span>{{ s.from_name }}</span>
            <i class="pi pi-arrow-right text-xs text-slate-400" />
            <span>{{ s.to_name }}</span>
            <span class="text-xs text-slate-400">{{ formatDate(s.created_at) }}</span>
            <span class="ml-auto font-medium tabular-nums">{{ money(s.amount_base) }}</span>
            <Button
              icon="pi pi-times"
              size="small"
              text
              severity="secondary"
              :loading="settling"
              v-tooltip.left="'Deshacer este pago'"
              @click="undo(s.id)"
            />
          </li>
        </TransitionGroup>
      </div>
    </template>
  </div>
</template>
