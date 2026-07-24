<script setup lang="ts">
import { computed, onMounted, ref, watch, TransitionGroup } from 'vue'
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Message from 'primevue/message'
import MemberChip from './MemberChip.vue'
import type { SettlementTransfer, Trip } from '../api/types'
import { useExpensesStore } from '../stores/expenses'
import { useTripsStore } from '../stores/trips'
import { formatDate, formatMoney } from '../composables/useMoney'
import { useNotify } from '../composables/useNotify'

const props = defineProps<{ trip: Trip }>()
const store = useExpensesStore()
const trips = useTripsStore()
const notify = useNotify()

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
    notify.success(`Pago registrado: ${transfer.from_name} → ${transfer.to_name}`)
    // refresca la pill de "deudas saldadas" del viaje
    await trips.loadTrip(props.trip.id)
  } catch (err) {
    notify.error('Error al liquidar', err)
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
    notify.error('Error al deshacer', err)
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
    <p v-if="data.common_count > 0" class="text-xs text-ink-faint flex items-center gap-1.5">
      <i class="pi pi-wallet" />
      {{ data.common_count }}
      {{ data.common_count === 1 ? 'gasto pagado' : 'gastos pagados' }} del fondo común
      ({{ money(data.common_total_base) }}): cuentan en los totales pero no generan deudas.
    </p>

    <p v-if="!data.balances.length" class="text-center text-sm text-ink-faint py-10">
      Añade viajeros al viaje y asigna pagadores a los gastos para ver los saldos.
    </p>

    <template v-else>
      <DataTable
        :value="data.balances"
        dataKey="traveler_id"
        size="small"
        class="bg-surface rounded-card overflow-hidden border border-line"
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
                b.net_base > 0 ? 'text-brand' : b.net_base < 0 ? 'text-red-600' : 'text-ink-faint'
              "
            >
              {{ b.net_base > 0 ? '+' : '' }}{{ money(b.net_base) }}
            </span>
          </template>
        </Column>
      </DataTable>

      <div
        v-if="data.debts_settled"
        class="tt-pop-in rounded-card border border-emerald-200 bg-brand-tint p-4 flex items-center gap-2 text-brand-strong font-medium"
      >
        <i class="pi pi-check-circle" />
        Deudas saldadas
      </div>

      <div v-else class="bg-surface rounded-card border border-line p-4">
        <h3 class="text-sm font-semibold text-ink mb-3">Liquidación sugerida</h3>
        <p v-if="!data.settlements.length" class="text-sm text-ink-faint flex items-center gap-1.5">
          <i class="pi pi-check-circle text-emerald-500" /> Todo cuadra: nadie debe nada.
        </p>
        <TransitionGroup v-else tag="ul" name="tt-list" class="relative flex flex-col gap-2">
          <li
            v-for="t in data.settlements"
            :key="`${t.from_id}-${t.to_id}`"
            class="flex items-center gap-2 text-sm text-ink"
          >
            <span class="font-medium">{{ t.from_name }}</span>
            <i class="pi pi-arrow-right text-xs text-ink-faint" />
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

      <div v-if="data.paid_settlements.length" class="bg-surface rounded-card border border-line p-4">
        <h3 class="text-sm font-semibold text-ink mb-3">Pagos registrados</h3>
        <TransitionGroup tag="ul" name="tt-list" class="relative flex flex-col gap-2">
          <li
            v-for="s in data.paid_settlements"
            :key="s.id"
            class="flex items-center gap-2 text-sm text-ink-secondary"
          >
            <i class="pi pi-check-circle text-emerald-500 text-xs" />
            <span>{{ s.from_name }}</span>
            <i class="pi pi-arrow-right text-xs text-ink-faint" />
            <span>{{ s.to_name }}</span>
            <span class="text-xs text-ink-faint">{{ formatDate(s.created_at) }}</span>
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
