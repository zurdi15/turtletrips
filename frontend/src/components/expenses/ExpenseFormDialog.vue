<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import DatePicker from 'primevue/datepicker'
import Select from 'primevue/select'
import AutoComplete from 'primevue/autocomplete'
import Button from 'primevue/button'
import Message from 'primevue/message'
import AttachmentList from '../AttachmentList.vue'
import ExpenseSplitEditor, { type SplitState } from '../ExpenseSplitEditor.vue'
import PayerSelect from '../PayerSelect.vue'
import FormDialog from '../ui/FormDialog.vue'
import FormField from '../ui/FormField.vue'
import UploadButton from '../ui/UploadButton.vue'
import { api } from '../../api/client'
import type { Expense, Place, RateRead, Trip } from '../../api/types'
import { CURRENCIES } from '../../constants'
import { intlLocale } from '../../i18n'
import { useExpensesStore } from '../../stores/expenses'
import { useAttachmentsStore } from '../../stores/attachments'
import { useCategoriesStore } from '../../stores/categories'
import { usePlacesStore } from '../../stores/places'
import { validateSplit } from '../../composables/useSplit'
import { useFormDialog } from '../../composables/useFormDialog'
import { useNotify } from '../../composables/useNotify'
import { formatMoney, parseIsoDate, toIsoDate } from '../../composables/useMoney'

const props = defineProps<{ trip: Trip; expense?: Expense | null }>()
const visible = defineModel<boolean>('visible', { required: true })
const emit = defineEmits<{ saved: [] }>()

const { t } = useI18n()
const notify = useNotify()
const store = useExpensesStore()
const attachmentsStore = useAttachmentsStore()
const categoriesStore = useCategoriesStore()
const places = usePlacesStore()

const numberLocale = computed(() => intlLocale())

onMounted(() => categoriesStore.load('expense'))

const day = ref<Date>(new Date())
const category = ref('Otros')
const description = ref('')
const amount = ref<number | null>(null)
const currency = ref('EUR')
const exchangeRate = ref<number | null>(null)
// 'common' = pagado del fondo/monedero común (no entra en los saldos)
const paidById = ref<number | 'common' | null>(null)
const placeValue = ref<string | Place>('')
const placeSuggestions = ref<Place[]>([])
const notes = ref('')
const split = ref<SplitState>({ split_mode: 'equal', shares: [] })
const fetchingRate = ref(false)
const rateSource = ref<string | null>(null)
// recibo elegido ANTES de crear el gasto: se sube justo después del create
const pendingReceipt = ref<File | null>(null)

function searchPlaces(query: string) {
  const q = query.trim().toLowerCase()
  placeSuggestions.value = places.items.filter((p) => !q || p.name.toLowerCase().includes(q))
}

const categoryOptions = computed(() => {
  const options = categoriesStore.expense.map((c) => ({ value: c.name, label: c.name }))
  // categoría huérfana de un gasto antiguo: se mantiene seleccionable
  if (category.value && !options.some((o) => o.value === category.value)) {
    options.push({ value: category.value, label: category.value })
  }
  return options
})
const isForeign = computed(() => currency.value !== props.trip.base_currency)
const converted = computed(() => {
  if (!isForeign.value || amount.value == null || exchangeRate.value == null) return null
  return amount.value * exchangeRate.value
})

watch([currency, day], async () => {
  if (!visible.value) return
  if (!isForeign.value) {
    exchangeRate.value = null
    rateSource.value = null
    return
  }
  await fetchRate()
})

async function fetchRate() {
  fetchingRate.value = true
  rateSource.value = null
  try {
    const rate = await api.get<RateRead>(
      `/rates?from=${currency.value}&to=${props.trip.base_currency}&date=${toIsoDate(day.value)}`,
    )
    exchangeRate.value = rate.rate
    rateSource.value = rate.source
  } catch {
    rateSource.value = 'error'
  } finally {
    fetchingRate.value = false
  }
}

const { saving, save } = useFormDialog({
  visible,
  entity: () => props.expense,
  reset(e) {
    if (places.tripId !== props.trip.id) places.load(props.trip.id)
    day.value = e ? parseIsoDate(e.day) : new Date()
    category.value = e?.category ?? 'Otros'
    description.value = e?.description ?? ''
    amount.value = e?.amount ?? null
    currency.value = e?.currency ?? props.trip.base_currency
    exchangeRate.value = e && e.currency !== props.trip.base_currency ? e.exchange_rate : null
    paidById.value = e?.paid_by_common ? 'common' : (e?.paid_by_id ?? null)
    placeValue.value = (e?.place_id != null && places.items.find((p) => p.id === e.place_id)) || ''
    notes.value = e?.notes ?? ''
    split.value = {
      split_mode: e?.split_mode ?? 'equal',
      shares: e?.shares.map((s) => ({ ...s })) ?? [],
    }
    rateSource.value = null
    pendingReceipt.value = null
  },
  validate() {
    if (!description.value.trim() || amount.value == null || amount.value <= 0) {
      return t('expenses.form.missingFields')
    }
    if (isForeign.value && exchangeRate.value == null) {
      return {
        summary: t('expenses.form.missingRate'),
        detail: t('expenses.form.missingRateDetail'),
      }
    }
    if (paidById.value !== 'common' && split.value.shares.length) {
      const splitError = validateSplit(
        split.value.split_mode,
        amount.value,
        split.value.shares.map((s) => s.value),
      )
      if (splitError)
        return {
          summary: t('expenses.form.splitIncomplete'),
          detail: t(splitError.key, splitError.params ?? {}),
        }
    }
    return null
  },
  async submit() {
    // sitio: uno existente, o crear uno nuevo que aparecerá en la pestaña Sitios
    let placeId: number | null = null
    if (typeof placeValue.value === 'object' && placeValue.value) {
      placeId = placeValue.value.id
    } else if (typeof placeValue.value === 'string' && placeValue.value.trim()) {
      const name = placeValue.value.trim()
      const existing = places.items.find((p) => p.name.toLowerCase() === name.toLowerCase())
      if (existing) {
        placeId = existing.id
      } else {
        const created = await places.create({ name, category: 'other' })
        placeId = created.id
        notify.info(t('expenses.toast.placeCreated', { name }))
      }
    }
    const payload = {
      day: toIsoDate(day.value),
      category: category.value,
      description: description.value.trim(),
      amount: amount.value!,
      currency: currency.value,
      exchange_rate: isForeign.value ? exchangeRate.value : 1,
      paid_by_id: paidById.value === 'common' ? null : paidById.value,
      paid_by_common: paidById.value === 'common',
      place_id: placeId,
      // del fondo común no hay reparto que hacer: se resetea al implícito
      split_mode: paidById.value === 'common' ? ('equal' as const) : split.value.split_mode,
      shares: paidById.value === 'common' ? [] : split.value.shares,
      notes: notes.value || null,
    }
    if (props.expense) return store.update(props.expense.id, payload)
    const created = await store.create(payload)
    // recibo elegido durante la creación: se sube ya con el gasto recién nacido
    if (pendingReceipt.value) {
      try {
        await attachmentsStore.upload(pendingReceipt.value, null, created.id)
      } catch (err) {
        notify.error(t('common.attachments.uploadError'), err)
      }
    }
    return created
  },
  onSaved: () => emit('saved'),
})
</script>

<template>
  <FormDialog
    v-model:visible="visible"
    :header="expense ? $t('expenses.form.editTitle') : $t('expenses.form.newTitle')"
    :saving="saving"
    :saveLabel="expense ? $t('common.actions.save') : $t('expenses.form.addLabel')"
    @save="save"
  >
    <div class="grid grid-cols-2 gap-3">
      <FormField :label="$t('expenses.fields.date')" required>
        <DatePicker v-model="day" showIcon dateFormat="dd/mm/yy" />
      </FormField>
      <FormField :label="$t('expenses.fields.category')">
        <Select
          v-model="category"
          :options="categoryOptions"
          optionLabel="label"
          optionValue="value"
        />
      </FormField>
    </div>
    <FormField :label="$t('expenses.fields.description')" required>
      <InputText v-model="description" :placeholder="$t('expenses.form.descriptionPlaceholder')" autofocus />
    </FormField>
    <div class="grid grid-cols-2 gap-3">
      <FormField :label="$t('expenses.fields.amount')" required>
        <InputNumber
          v-model="amount"
          :minFractionDigits="0"
          :maxFractionDigits="2"
          :locale="numberLocale"
          :min="0"
        />
      </FormField>
      <FormField :label="$t('expenses.fields.currency')">
        <Select v-model="currency" :options="CURRENCIES" filter />
      </FormField>
    </div>

    <div v-if="isForeign" class="rounded-lg bg-surface-soft border border-line p-3">
      <div class="flex items-end gap-3">
        <div class="flex flex-col gap-1 flex-1">
          <label class="text-sm font-medium">
            {{ $t('expenses.form.exchangeRate', { from: currency, to: trip.base_currency }) }}
          </label>
          <InputNumber
            v-model="exchangeRate"
            :minFractionDigits="2"
            :maxFractionDigits="6"
            :locale="numberLocale"
          />
        </div>
        <Button
          icon="pi pi-refresh"
          severity="secondary"
          outlined
          :loading="fetchingRate"
          v-tooltip.top="$t('expenses.form.fetchRate')"
          @click="fetchRate"
        />
      </div>
      <p v-if="converted != null" class="text-sm text-ink-secondary mt-2">
        ≈ <strong>{{ formatMoney(converted, trip.base_currency) }}</strong>
        <span v-if="rateSource === 'cache'" class="text-ink-faint"> {{ $t('expenses.form.rateCached') }}</span>
        <span v-else-if="rateSource === 'api'" class="text-ink-faint"> {{ $t('expenses.form.rateApi') }}</span>
      </p>
      <Message v-if="rateSource === 'error'" severity="warn" size="small" class="mt-2">
        {{ $t('expenses.form.rateError') }}
      </Message>
    </div>

    <div class="grid grid-cols-2 gap-3">
      <FormField :label="$t('expenses.fields.paidBy')">
        <PayerSelect v-model="paidById" :travelers="trip.travelers" />
      </FormField>
      <FormField :label="$t('expenses.fields.place')">
        <AutoComplete
          v-model="placeValue"
          :suggestions="placeSuggestions"
          optionLabel="name"
          dropdown
          :placeholder="$t('expenses.form.placePlaceholder')"
          @complete="(e) => searchPlaces(e.query)"
        />
      </FormField>
    </div>
    <ExpenseSplitEditor
      v-if="paidById !== 'common'"
      v-model="split"
      :travelers="trip.travelers"
      :amount="amount"
      :currency="currency"
    />
    <p v-else class="text-xs text-ink-faint rounded-lg bg-surface-soft border border-line p-3">
      <i class="pi pi-wallet mr-1" />{{ $t('expenses.form.commonNote') }}
    </p>

    <FormField :label="$t('expenses.fields.notes')">
      <InputText v-model="notes" :placeholder="$t('expenses.form.notesPlaceholder')" />
    </FormField>

    <!-- recibo (foto o PDF): al editar gestiona los adjuntos del gasto; al
         crear se deja elegido y se sube nada más guardar -->
    <div class="pt-3 border-t border-line-subtle">
      <p class="text-sm font-medium mb-2">{{ $t('expenses.form.receipt') }}</p>
      <AttachmentList v-if="expense" :expense-id="expense.id" />
      <template v-else>
        <div
          v-if="pendingReceipt"
          class="flex items-center gap-2 bg-surface-soft border border-line rounded-lg px-2.5 py-1.5 text-sm mb-2"
        >
          <i class="pi pi-paperclip shrink-0" />
          <span class="flex-1 min-w-0 truncate">{{ pendingReceipt.name }}</span>
          <button
            type="button"
            class="flex items-center text-ink-faint hover:text-ink cursor-pointer"
            @click="pendingReceipt = null"
          >
            <i class="pi pi-times-circle text-xs" />
          </button>
        </div>
        <UploadButton
          :label="$t('common.attachments.attach')"
          icon="pi pi-paperclip"
          severity="secondary"
          outlined
          size="small"
          accept="application/pdf,image/*"
          @file="(f) => (pendingReceipt = f)"
        />
      </template>
    </div>
  </FormDialog>
</template>
