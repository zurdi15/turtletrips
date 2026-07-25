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
      <div class="bg-surface rounded-card border border-line p-3.5">
        <p class="text-2xs uppercase tracking-wide text-ink-faint font-semibold">
          {{ $t('expenses.stats.total') }}
        </p>
        <p class="text-xl font-bold text-ink-heading mt-1 tabular-nums">
          {{ formatMoney(total ?? 0, currency) }}
        </p>
        <p class="text-xs text-ink-faint mt-0.5">{{ $t('expenses.stats.count', { n: stats.count }) }}</p>
      </div>
      <div class="bg-surface rounded-card border border-line p-3.5">
        <p class="text-2xs uppercase tracking-wide text-ink-faint font-semibold">{{ $t('expenses.stats.budget') }}</p>
        <p class="text-xl font-bold text-ink-heading mt-1">
          {{
            summary?.budget_amount != null ? formatMoney(summary.budget_amount, currency) : '—'
          }}
        </p>
        <div v-if="budgetPct != null" class="mt-1.5">
          <ProgressMeter :value="budgetPct" thresholds size="xs" />
          <p class="text-xs text-ink-faint mt-0.5">{{ $t('expenses.stats.budgetUsed', { pct: budgetPct }) }}</p>
        </div>
      </div>
      <div class="bg-surface rounded-card border border-line p-3.5">
        <p class="text-2xs uppercase tracking-wide text-ink-faint font-semibold">{{ $t('expenses.stats.remaining') }}</p>
        <p
          class="text-xl font-bold mt-1 tabular-nums"
          :class="(summary?.remaining ?? 0) < 0 ? 'text-red-600' : 'text-brand'"
        >
          {{ summary?.remaining != null ? formatMoney(remaining ?? 0, currency) : '—' }}
        </p>
        <p class="text-xs text-ink-faint mt-0.5">{{ $t('expenses.stats.remainingHint') }}</p>
      </div>
      <div class="bg-surface rounded-card border border-line p-3.5">
        <p class="text-2xs uppercase tracking-wide text-ink-faint font-semibold">{{ $t('expenses.stats.perPerson') }}</p>
        <p class="text-xl font-bold text-ink-heading mt-1 tabular-nums">
          {{ stats.perPerson != null ? formatMoney(perPerson ?? 0, currency) : '—' }}
        </p>
        <p class="text-xs text-ink-faint mt-0.5">
          {{
            stats.travelers
              ? $t('expenses.stats.perPersonHint', { n: stats.travelers })
              : $t('expenses.stats.perPersonEmpty')
          }}
        </p>
      </div>
      <div class="bg-surface rounded-card border border-line p-3.5">
        <p class="text-2xs uppercase tracking-wide text-ink-faint font-semibold">{{ $t('expenses.stats.perDay') }}</p>
        <p class="text-xl font-bold text-ink-heading mt-1 tabular-nums">
          {{ stats.perDay != null ? formatMoney(perDay ?? 0, currency) : '—' }}
        </p>
        <p class="text-xs text-ink-faint mt-0.5">
          {{ stats.days ? $t('expenses.stats.days', { n: stats.days }) : $t('expenses.stats.noDates') }}
        </p>
      </div>
      <div class="bg-surface rounded-card border border-line p-3.5">
        <p class="text-2xs uppercase tracking-wide text-ink-faint font-semibold">
          {{ $t('expenses.stats.perDayPerson') }}
        </p>
        <p class="text-xl font-bold text-ink-heading mt-1 tabular-nums">
          {{ stats.perDayPerson != null ? formatMoney(perDayPerson ?? 0, currency) : '—' }}
        </p>
        <p v-if="activeFilterCount" class="text-xs text-info mt-0.5">{{ $t('expenses.stats.filtered') }}</p>
      </div>
    </div>

    <p
      v-if="currencyBreakdown.length"
      class="text-xs text-ink-faint -mt-3 mb-4 flex flex-wrap gap-x-3"
    >
      <span>{{ $t('expenses.stats.originalCurrency') }}</span>
      <span v-for="[cur, amount] in currencyBreakdown" :key="cur">
        {{ formatMoney(amount, cur) }}
      </span>
    </p>
  </div>
</template>
