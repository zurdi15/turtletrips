<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import type { TripSummary } from '../../api/types'
import type { ExpenseStats } from '../../utils/expenses'
import { formatMoney } from '../../composables/useMoney'
import { useAnimatedNumber } from '../../composables/useAnimatedNumber'
import { useMediaQuery } from '../../composables/useMediaQuery'
import CollapsePanel from '../ui/CollapsePanel.vue'
import ProgressMeter from '../ui/ProgressMeter.vue'

const props = defineProps<{
  stats: ExpenseStats
  summary: TripSummary | null
  budgetPct: number | null
  currency: string
  activeFilterCount: number
  currencyBreakdown: [string, number][]
}>()

const { t } = useI18n()

// en móvil solo total y presupuesto a la vista; el resto en un colapsable
const isDesktop = useMediaQuery('(min-width: 640px)')
const showMore = ref(false)

// los importes cuentan hasta su valor (y persiguen los cambios de filtros)
const total = useAnimatedNumber(() => props.stats.total)
const remaining = useAnimatedNumber(() => props.summary?.remaining)
const perPerson = useAnimatedNumber(() => props.stats.perPerson)
const perDay = useAnimatedNumber(() => props.stats.perDay)
const perDayPerson = useAnimatedNumber(() => props.stats.perDayPerson)

// tarjetas secundarias: mismo markup en el grid (desktop) y en el colapsable
// (móvil); computed para que reaccionen al idioma y a los números animados
const extraCards = computed(() => [
  {
    key: 'remaining',
    label: t('expenses.stats.remaining'),
    value: props.summary?.remaining != null ? formatMoney(remaining.value ?? 0, props.currency) : '—',
    valueClass: (props.summary?.remaining ?? 0) < 0 ? 'text-red-600' : 'text-brand',
    hint: t('expenses.stats.remainingHint'),
  },
  {
    key: 'perPerson',
    label: t('expenses.stats.perPerson'),
    value: props.stats.perPerson != null ? formatMoney(perPerson.value ?? 0, props.currency) : '—',
    hint: props.stats.travelers
      ? t('expenses.stats.perPersonHint', { n: props.stats.travelers })
      : t('expenses.stats.perPersonEmpty'),
  },
  {
    key: 'perDay',
    label: t('expenses.stats.perDay'),
    value: props.stats.perDay != null ? formatMoney(perDay.value ?? 0, props.currency) : '—',
    hint: props.stats.days ? t('expenses.stats.days', { n: props.stats.days }) : t('expenses.stats.noDates'),
  },
  {
    key: 'perDayPerson',
    label: t('expenses.stats.perDayPerson'),
    value: props.stats.perDayPerson != null ? formatMoney(perDayPerson.value ?? 0, props.currency) : '—',
    hint: props.activeFilterCount ? t('expenses.stats.filtered') : undefined,
    hintClass: 'text-info',
  },
])
</script>

<template>
  <div>
    <div class="tt-stagger grid grid-cols-2 gap-3 mb-2 sm:mb-5 sm:grid-cols-3 xl:grid-cols-6">
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
      <template v-if="isDesktop">
        <div v-for="card in extraCards" :key="card.key" class="bg-surface rounded-card border border-line p-3.5">
          <p class="text-2xs uppercase tracking-wide text-ink-faint font-semibold">{{ card.label }}</p>
          <p class="text-xl font-bold mt-1 tabular-nums" :class="card.valueClass ?? 'text-ink-heading'">
            {{ card.value }}
          </p>
          <p v-if="card.hint" class="text-xs mt-0.5" :class="card.hintClass ?? 'text-ink-faint'">
            {{ card.hint }}
          </p>
        </div>
      </template>
    </div>

    <p
      v-if="isDesktop && currencyBreakdown.length"
      class="text-xs text-ink-faint -mt-3 mb-4 flex flex-wrap gap-x-3"
    >
      <span>{{ $t('expenses.stats.originalCurrency') }}</span>
      <span v-for="[cur, amount] in currencyBreakdown" :key="cur">
        {{ formatMoney(amount, cur) }}
      </span>
    </p>

    <template v-if="!isDesktop">
      <CollapsePanel :open="showMore">
        <div class="pt-1 pb-1">
          <div class="grid grid-cols-2 gap-3">
            <div v-for="card in extraCards" :key="card.key" class="bg-surface rounded-card border border-line p-3.5">
              <p class="text-2xs uppercase tracking-wide text-ink-faint font-semibold">{{ card.label }}</p>
              <p class="text-xl font-bold mt-1 tabular-nums" :class="card.valueClass ?? 'text-ink-heading'">
                {{ card.value }}
              </p>
              <p v-if="card.hint" class="text-xs mt-0.5" :class="card.hintClass ?? 'text-ink-faint'">
                {{ card.hint }}
              </p>
            </div>
          </div>
          <p v-if="currencyBreakdown.length" class="mt-2 text-xs text-ink-faint flex flex-wrap gap-x-3">
            <span>{{ $t('expenses.stats.originalCurrency') }}</span>
            <span v-for="[cur, amount] in currencyBreakdown" :key="cur">
              {{ formatMoney(amount, cur) }}
            </span>
          </p>
        </div>
      </CollapsePanel>
      <Button
        text
        size="small"
        severity="secondary"
        class="w-full mb-3"
        :icon="showMore ? 'pi pi-chevron-up' : 'pi pi-chevron-down'"
        :label="showMore ? $t('expenses.stats.showLess') : $t('expenses.stats.showMore')"
        @click="showMore = !showMore"
      />
    </template>
  </div>
</template>
