<script setup lang="ts">
import type { TripSummary } from '../../api/types'
import type { ExpenseStats } from '../../utils/expenses'
import { formatMoney } from '../../composables/useMoney'
import { useAnimatedNumber } from '../../composables/useAnimatedNumber'
import ProgressMeter from '../ui/ProgressMeter.vue'

const props = defineProps<{
  stats: ExpenseStats
  summary: TripSummary | null
  budgetPct: number | null
  currency: string
  activeFilterCount: number
  currencyBreakdown: [string, number][]
}>()

// los importes cuentan hasta su valor (y persiguen los cambios de filtros)
const total = useAnimatedNumber(() => props.stats.total)
const remaining = useAnimatedNumber(() => props.summary?.remaining)
const perPerson = useAnimatedNumber(() => props.stats.perPerson)
const perDay = useAnimatedNumber(() => props.stats.perDay)
const perDayPerson = useAnimatedNumber(() => props.stats.perDayPerson)
</script>

<template>
  <div>
    <div class="tt-stagger grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-6 gap-3 mb-5">
      <div class="bg-white rounded-xl border border-slate-200 p-3.5">
        <p class="text-[11px] uppercase tracking-wide text-slate-400 font-semibold">
          Total gastado
        </p>
        <p class="text-xl font-bold text-slate-800 mt-1 tabular-nums">
          {{ formatMoney(total ?? 0, currency) }}
        </p>
        <p class="text-xs text-slate-400 mt-0.5">{{ stats.count }} gastos</p>
      </div>
      <div class="bg-white rounded-xl border border-slate-200 p-3.5">
        <p class="text-[11px] uppercase tracking-wide text-slate-400 font-semibold">Presupuesto</p>
        <p class="text-xl font-bold text-slate-800 mt-1">
          {{
            summary?.budget_amount != null ? formatMoney(summary.budget_amount, currency) : '—'
          }}
        </p>
        <div v-if="budgetPct != null" class="mt-1.5">
          <ProgressMeter :value="budgetPct" thresholds size="xs" />
          <p class="text-xs text-slate-400 mt-0.5">{{ budgetPct }}% usado</p>
        </div>
      </div>
      <div class="bg-white rounded-xl border border-slate-200 p-3.5">
        <p class="text-[11px] uppercase tracking-wide text-slate-400 font-semibold">Restante</p>
        <p
          class="text-xl font-bold mt-1 tabular-nums"
          :class="(summary?.remaining ?? 0) < 0 ? 'text-red-600' : 'text-emerald-600'"
        >
          {{ summary?.remaining != null ? formatMoney(remaining ?? 0, currency) : '—' }}
        </p>
        <p class="text-xs text-slate-400 mt-0.5">del presupuesto del viaje</p>
      </div>
      <div class="bg-white rounded-xl border border-slate-200 p-3.5">
        <p class="text-[11px] uppercase tracking-wide text-slate-400 font-semibold">Por persona</p>
        <p class="text-xl font-bold text-slate-800 mt-1 tabular-nums">
          {{ stats.perPerson != null ? formatMoney(perPerson ?? 0, currency) : '—' }}
        </p>
        <p class="text-xs text-slate-400 mt-0.5">
          {{ stats.travelers ? `entre ${stats.travelers} viajeros` : 'añade viajeros al viaje' }}
        </p>
      </div>
      <div class="bg-white rounded-xl border border-slate-200 p-3.5">
        <p class="text-[11px] uppercase tracking-wide text-slate-400 font-semibold">Por día</p>
        <p class="text-xl font-bold text-slate-800 mt-1 tabular-nums">
          {{ stats.perDay != null ? formatMoney(perDay ?? 0, currency) : '—' }}
        </p>
        <p class="text-xs text-slate-400 mt-0.5">
          {{ stats.days ? `${stats.days} días` : 'sin fechas' }}
        </p>
      </div>
      <div class="bg-white rounded-xl border border-slate-200 p-3.5">
        <p class="text-[11px] uppercase tracking-wide text-slate-400 font-semibold">
          Por día y persona
        </p>
        <p class="text-xl font-bold text-slate-800 mt-1 tabular-nums">
          {{ stats.perDayPerson != null ? formatMoney(perDayPerson ?? 0, currency) : '—' }}
        </p>
        <p v-if="activeFilterCount" class="text-xs text-sky-600 mt-0.5">con filtros aplicados</p>
      </div>
    </div>

    <p
      v-if="currencyBreakdown.length"
      class="text-xs text-slate-400 -mt-3 mb-4 flex flex-wrap gap-x-3"
    >
      <span>En moneda original:</span>
      <span v-for="[cur, amount] in currencyBreakdown" :key="cur">
        {{ formatMoney(amount, cur) }}
      </span>
    </p>
  </div>
</template>
