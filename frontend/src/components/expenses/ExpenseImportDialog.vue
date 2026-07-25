<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Message from 'primevue/message'
import Tag from 'primevue/tag'
import UploadButton from '../ui/UploadButton.vue'
import type { ImportResult, Trip } from '../../api/types'
import { useExpensesStore } from '../../stores/expenses'
import { formatDate, formatMoney } from '../../composables/useMoney'
import { useNotify } from '../../composables/useNotify'

const props = defineProps<{ trip: Trip }>()
const visible = defineModel<boolean>('visible', { required: true })
const emit = defineEmits<{ imported: [count: number] }>()

const { t } = useI18n()
const notify = useNotify()
const store = useExpensesStore()

const file = ref<File | null>(null)
const preview = ref<ImportResult | null>(null)
const loading = ref(false)
const importing = ref(false)

function reset() {
  file.value = null
  preview.value = null
}

async function onFileChosen(chosen: File) {
  file.value = chosen
  loading.value = true
  try {
    preview.value = await store.importCsv(chosen, true)
  } catch (err) {
    notify.error(t('expenses.import.readError'), err)
    reset()
  } finally {
    loading.value = false
  }
}

async function confirmImport() {
  if (!file.value) return
  importing.value = true
  try {
    const result = await store.importCsv(file.value, false)
    notify.success(t('expenses.import.imported', { n: result.imported }))
    emit('imported', result.imported)
    visible.value = false
    reset()
  } catch (err) {
    notify.error(t('expenses.import.importError'), err)
  } finally {
    importing.value = false
  }
}

</script>

<template>
  <Dialog
    v-model:visible="visible"
    modal
    :header="$t('expenses.import.title')"
    class="w-full max-w-3xl mx-4"
    @hide="reset"
  >
    <div v-if="!preview" class="flex flex-col gap-4">
      <p class="text-sm text-ink-secondary">
        {{ $t('expenses.import.introColumns') }}
        <code class="text-xs bg-surface-muted px-1 rounded">{{ $t('expenses.import.columnsExample') }}</code>
        {{ $t('expenses.import.introAmounts') }}
        <code class="text-xs bg-surface-muted px-1 rounded">1.528,00 €</code> {{ $t('expenses.import.introDates') }}
        <code class="text-xs bg-surface-muted px-1 rounded">{{ $t('expenses.import.dateFormat') }}</code> {{ $t('expenses.import.or') }}
        <code class="text-xs bg-surface-muted px-1 rounded">10 febrero 2026</code>.
        {{ $t('expenses.import.introRest') }}
      </p>
      <UploadButton
        :label="$t('expenses.import.chooseFile')"
        icon="pi pi-upload"
        accept=".csv,text/csv"
        :loading="loading"
        @file="onFileChosen"
      />
    </div>

    <div v-else class="flex flex-col gap-4">
      <div class="flex items-center gap-3 flex-wrap">
        <Tag :value="$t('expenses.import.validRows', { n: preview.valid_rows.length })" severity="success" />
        <Tag
          v-if="preview.errors.length"
          :value="$t('expenses.import.errorRows', { n: preview.errors.length })"
          severity="danger"
        />
        <Button
          :label="$t('expenses.import.chooseAnother')"
          severity="secondary"
          text
          size="small"
          icon="pi pi-arrow-left"
          @click="reset"
        />
      </div>

      <Message v-if="preview.errors.length" severity="warn" size="small">
        <ul class="m-0 pl-4">
          <li v-for="err in preview.errors.slice(0, 8)" :key="err.row">
            {{ $t('expenses.import.rowError', { row: err.row, error: err.error }) }}
          </li>
          <li v-if="preview.errors.length > 8">{{ $t('expenses.import.moreErrors', { n: preview.errors.length - 8 }) }}</li>
        </ul>
      </Message>

      <DataTable
        :value="preview.valid_rows"
        size="small"
        scrollable
        scrollHeight="320px"
        :tableStyle="{ minWidth: '540px' }"
        class="text-sm"
      >
        <Column :header="$t('expenses.fields.date')">
          <template #body="{ data }">{{ formatDate(data.day) }}</template>
        </Column>
        <Column field="category" :header="$t('expenses.fields.category')" />
        <Column field="description" :header="$t('expenses.fields.description')" />
        <Column :header="$t('expenses.fields.amount')">
          <template #body="{ data }">{{ formatMoney(data.amount, data.currency) }}</template>
        </Column>
        <Column :header="$t('expenses.import.inCurrency', { currency: trip.base_currency })">
          <template #body="{ data }">{{ formatMoney(data.amount_base, trip.base_currency) }}</template>
        </Column>
        <Column field="paid_by" :header="$t('expenses.fields.paidBy')" />
        <Column field="place" :header="$t('expenses.fields.place')" />
        <Column field="notes" :header="$t('expenses.fields.notes')" />
      </DataTable>
    </div>

    <template #footer>
      <Button :label="$t('common.actions.cancel')" severity="secondary" text @click="visible = false" />
      <Button
        v-if="preview"
        :label="$t('expenses.import.confirm', { n: preview.valid_rows.length })"
        icon="pi pi-check"
        :disabled="!preview.valid_rows.length"
        :loading="importing"
        @click="confirmImport"
      />
    </template>
  </Dialog>
</template>
