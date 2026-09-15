<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputNumber from 'primevue/inputnumber'
import Select from 'primevue/select'
import { api } from '../../api/client'
import type { RateRead } from '../../api/types'
import { CURRENCIES } from '../../constants'
import { formatDate, formatMoney } from '../../composables/useMoney'
import { intlLocale } from '../../i18n'

// Conversor de divisas de bolsillo: usa el mismo endpoint de tasas que los
// gastos (caché en DB → frankfurter → proveedor de respaldo), así que las
// monedas que valen aquí son exactamente las que valen en un gasto.
const props = defineProps<{ baseCurrency: string }>()
const visible = defineModel<boolean>('visible', { required: true })
const { t } = useI18n()

const amount = ref<number | null>(1)
const from = ref(props.baseCurrency)
const to = ref('USD')
const rate = ref<RateRead | null>(null)
const loading = ref(false)
const failed = ref(false)
const numberLocale = computed(() => intlLocale())

let timer: ReturnType<typeof setTimeout> | undefined
let seq = 0

async function fetchRate() {
  const mySeq = ++seq
  if (from.value === to.value) {
    rate.value = null
    failed.value = false
    return
  }
  loading.value = true
  failed.value = false
  try {
    const r = await api.get<RateRead>(`/rates?from=${from.value}&to=${to.value}`)
    if (mySeq === seq) rate.value = r
  } catch {
    if (mySeq === seq) {
      rate.value = null
      failed.value = true
    }
  } finally {
    if (mySeq === seq) loading.value = false
  }
}

watch([from, to], () => {
  if (timer) clearTimeout(timer)
  timer = setTimeout(fetchRate, 250)
})

watch(visible, (open) => {
  if (!open) return
  // se abre siempre desde la moneda del viaje; el destino se conserva
  from.value = props.baseCurrency
  if (to.value === from.value) to.value = from.value === 'USD' ? 'EUR' : 'USD'
  fetchRate()
})

const result = computed(() => {
  if (amount.value == null) return null
  if (from.value === to.value) return amount.value
  return rate.value ? amount.value * rate.value.rate : null
})

// la tasa con cifras significativas, no con dos decimales: VND→EUR es 0,000033
const rateText = computed(() =>
  rate.value ? rate.value.rate.toLocaleString(intlLocale(), { maximumSignificantDigits: 6 }) : '',
)

function swap() {
  const f = from.value
  from.value = to.value
  to.value = f
}
</script>

<template>
  <Dialog v-model:visible="visible" modal :header="t('expenses.converter.title')" class="w-full mx-4 max-w-md">
    <div class="flex flex-col gap-4">
      <div class="grid grid-cols-[minmax(0,1fr)_auto] gap-3 items-end">
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">{{ t('expenses.converter.amount') }}</label>
          <InputNumber
            v-model="amount"
            :minFractionDigits="0"
            :maxFractionDigits="2"
            :locale="numberLocale"
            :min="0"
            autofocus
          />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">{{ t('expenses.converter.from') }}</label>
          <Select v-model="from" :options="CURRENCIES" filter class="w-28" />
        </div>
      </div>

      <div class="flex items-center gap-3">
        <span class="flex-1 border-t border-line-subtle" />
        <Button
          icon="pi pi-arrow-right-arrow-left"
          severity="secondary"
          outlined
          rounded
          v-tooltip.top="t('expenses.converter.swap')"
          @click="swap"
        />
        <span class="flex-1 border-t border-line-subtle" />
      </div>

      <div class="grid grid-cols-[minmax(0,1fr)_auto] gap-3 items-end">
        <div class="flex flex-col gap-1 min-w-0">
          <label class="text-sm font-medium">{{ t('expenses.converter.to') }}</label>
          <div
            class="rounded-lg bg-surface-soft border border-line px-3 py-2 text-lg font-semibold text-ink tabular-nums truncate min-h-[2.75rem]"
          >
            <span v-if="result != null">{{ formatMoney(result, to) }}</span>
            <span v-else-if="loading" class="text-ink-faint text-sm">…</span>
            <span v-else class="text-ink-faint text-sm">—</span>
          </div>
        </div>
        <Select v-model="to" :options="CURRENCIES" filter class="w-28" />
      </div>

      <p v-if="rate" class="text-xs text-ink-faint">
        1 {{ rate.base }} = {{ rateText }} {{ rate.quote }}
        <span class="opacity-70">· {{ formatDate(rate.day) }}</span>
        <span v-if="rate.source === 'cache'" class="opacity-70"> · {{ t('expenses.form.rateCached') }}</span>
      </p>
      <p v-else-if="failed" class="text-xs text-warn-strong">
        {{ t('expenses.converter.unavailable', { from, to }) }}
      </p>
    </div>
  </Dialog>
</template>
