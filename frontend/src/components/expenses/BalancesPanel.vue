<script setup lang="ts">
import { computed, onMounted, ref, watch, TransitionGroup } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Message from 'primevue/message'
import MemberChip from '../MemberChip.vue'
import type { SettlementTransfer, Trip } from '../../api/types'
import { useExpensesStore } from '../../stores/expenses'
import { useTripsStore } from '../../stores/trips'
import { formatDate, formatMoney } from '../../composables/useMoney'
import { useMediaQuery } from '../../composables/useMediaQuery'
import { useNotify } from '../../composables/useNotify'

const props = defineProps<{ trip: Trip }>()
const { t } = useI18n()
const store = useExpensesStore()
const trips = useTripsStore()
const notify = useNotify()

// bajo `sm` la tabla se sustituye por tarjetas apiladas (sin scroll lateral)
const isDesktop = useMediaQuery('(min-width: 640px)')

onMounted(() => store.loadBalances())
watch(() => props.trip.id, () => store.loadBalances())

const data = computed(() => store.balances)
const money = (v: number) => formatMoney(v, props.trip.base_currency)

// los saldos solo traen id/nombre/color: el viajero del viaje añade su avatar
const memberById = computed(() => new Map(props.trip.travelers.map((tr) => [tr.id, tr])))

function chipOf(id: number, name: string, color: string | null = null) {
  return memberById.value.get(id) ?? { id, name, color }
}

function netClass(net: number): string {
  return net > 0 ? 'text-brand' : net < 0 ? 'text-red-600' : 'text-ink-faint'
}

const settling = ref(false)

async function settle(transfer: SettlementTransfer) {
  settling.value = true
  try {
    await store.settle({
      from_id: transfer.from_id,
      to_id: transfer.to_id,
      amount_base: transfer.amount_base,
    })
    notify.success(
      t('expenses.balances.toastSettled', { from: transfer.from_name, to: transfer.to_name }),
    )
    // refresca la pill de "deudas saldadas" del viaje
    await trips.loadTrip(props.trip.id)
  } catch (err) {
    notify.error(t('expenses.balances.settleError'), err)
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
    notify.error(t('expenses.balances.undoError'), err)
  } finally {
    settling.value = false
  }
}
</script>

<template>
  <div v-if="data" class="flex flex-col gap-4">
    <Message v-if="data.unassigned_count > 0" severity="warn" size="small">
      {{
        $t(
          'expenses.balances.unassignedWarning',
          { n: data.unassigned_count, amount: money(data.unassigned_total_base) },
          data.unassigned_count,
        )
      }}
    </Message>
    <p v-if="data.common_count > 0" class="text-xs text-ink-faint flex items-center gap-1.5">
      <i class="pi pi-wallet" />
      {{
        $t(
          'expenses.balances.commonInfo',
          { n: data.common_count, amount: money(data.common_total_base) },
          data.common_count,
        )
      }}
    </p>

    <p v-if="!data.balances.length" class="text-center text-sm text-ink-faint py-10">
      {{ $t('expenses.balances.empty') }}
    </p>

    <template v-else>
      <DataTable
        v-if="isDesktop"
        :value="data.balances"
        dataKey="traveler_id"
        size="small"
        class="bg-surface rounded-card overflow-hidden border border-line"
      >
        <Column :header="$t('expenses.balances.columns.traveler')">
          <template #body="{ data: b }">
            <MemberChip :member="chipOf(b.traveler_id, b.name, b.color)" />
          </template>
        </Column>
        <Column :header="$t('expenses.balances.columns.paid')">
          <template #body="{ data: b }">
            <span class="tabular-nums">{{ money(b.paid_base) }}</span>
          </template>
        </Column>
        <Column :header="$t('expenses.balances.columns.owed')">
          <template #body="{ data: b }">
            <span class="tabular-nums">{{ money(b.owed_base) }}</span>
          </template>
        </Column>
        <Column :header="$t('expenses.balances.columns.net')">
          <template #body="{ data: b }">
            <span class="font-semibold tabular-nums" :class="netClass(b.net_base)">
              {{ b.net_base > 0 ? '+' : '' }}{{ money(b.net_base) }}
            </span>
          </template>
        </Column>
      </DataTable>

      <!-- móvil: una tarjeta por viajero — saldo grande y el desglose debajo -->
      <ul
        v-else
        class="tt-stagger bg-surface rounded-card overflow-hidden border border-line divide-y divide-line-subtle"
      >
        <li
          v-for="b in data.balances"
          :key="b.traveler_id"
          class="flex items-center px-4 py-3"
        >
          <MemberChip :member="chipOf(b.traveler_id, b.name, b.color)" />
          <div class="ml-auto text-right">
            <div class="text-sm font-semibold tabular-nums" :class="netClass(b.net_base)">
              {{ b.net_base > 0 ? '+' : '' }}{{ money(b.net_base) }}
            </div>
          </div>
        </li>
      </ul>

      <div
        v-if="data.debts_settled"
        class="tt-pop-in rounded-card border border-emerald-200 bg-brand-tint p-4 flex items-center gap-2 text-brand-strong font-medium"
      >
        <i class="pi pi-check-circle" />
        {{ $t('expenses.balances.settled') }}
      </div>

      <div v-else class="bg-surface rounded-card border border-line p-4">
        <h3 class="text-sm font-semibold text-ink mb-3">{{ $t('expenses.balances.suggestedTitle') }}</h3>
        <p v-if="!data.settlements.length" class="text-sm text-ink-faint flex items-center gap-1.5">
          <i class="pi pi-check-circle text-emerald-500" /> {{ $t('expenses.balances.allSquare') }}
        </p>
        <TransitionGroup v-else tag="ul" name="tt-list" class="relative flex flex-col gap-2">
          <!-- flex-wrap: en móvil el botón baja a su propia línea en vez de
               empujar los chips fuera de la tarjeta -->
          <li
            v-for="t in data.settlements"
            :key="`${t.from_id}-${t.to_id}`"
            class="flex flex-wrap items-center gap-2 text-sm text-ink"
          >
            <MemberChip :member="chipOf(t.from_id, t.from_name)" />
            <i class="pi pi-arrow-right text-xs text-ink-faint" />
            <MemberChip :member="chipOf(t.to_id, t.to_name)" />
            <span class="ml-auto font-semibold tabular-nums">{{ money(t.amount_base) }}</span>
            <!-- acción ligera: la sección son chips y cifras, un botón sólido
                 pesaba más que el propio saldo -->
            <Button
              :label="$t('expenses.balances.settle')"
              icon="pi pi-check"
              size="small"
              text
              class="max-sm:w-full"
              :loading="settling"
              v-tooltip.left="$t('expenses.balances.settleTooltip')"
              @click="settle(t)"
            />
          </li>
        </TransitionGroup>
      </div>

      <div v-if="data.paid_settlements.length" class="bg-surface rounded-card border border-line p-4">
        <h3 class="text-sm font-semibold text-ink mb-3">{{ $t('expenses.balances.paymentsTitle') }}</h3>
        <TransitionGroup tag="ul" name="tt-list" class="relative flex flex-col gap-2">
          <li
            v-for="s in data.paid_settlements"
            :key="s.id"
            class="flex flex-wrap items-center gap-2 text-sm text-ink-secondary"
          >
            <i class="pi pi-check-circle text-emerald-500 text-xs" />
            <MemberChip :member="chipOf(s.from_id, s.from_name)" />
            <i class="pi pi-arrow-right text-xs text-ink-faint" />
            <MemberChip :member="chipOf(s.to_id, s.to_name)" />
            <span class="text-xs text-ink-faint">{{ formatDate(s.created_at) }}</span>
            <span class="ml-auto font-medium tabular-nums">{{ money(s.amount_base) }}</span>
            <Button
              icon="pi pi-times"
              size="small"
              text
              severity="secondary"
              :loading="settling"
              v-tooltip.left="$t('expenses.balances.undoTooltip')"
              @click="undo(s.id)"
            />
          </li>
        </TransitionGroup>
      </div>
    </template>
  </div>
</template>

<style scoped>
/* size="small" deja las celdas muy apretadas: un poco más de aire, igual que
   en la tabla de gastos */
:deep(.p-datatable-thead > tr > th),
:deep(.p-datatable-tbody > tr > td) {
  padding: 0.625rem 1rem;
}
</style>
