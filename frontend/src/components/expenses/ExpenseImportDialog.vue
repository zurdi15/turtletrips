<script setup lang="ts">
import { ref } from 'vue'
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
    notify.error('Error leyendo el CSV', err)
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
    notify.success(`${result.imported} gastos importados`)
    emit('imported', result.imported)
    visible.value = false
    reset()
  } catch (err) {
    notify.error('Error al importar', err)
  } finally {
    importing.value = false
  }
}

</script>

<template>
  <Dialog
    v-model:visible="visible"
    modal
    header="Importar gastos desde CSV"
    class="w-full max-w-3xl mx-4"
    @hide="reset"
  >
    <div v-if="!preview" class="flex flex-col gap-4">
      <p class="text-sm text-ink-secondary">
        Sube un CSV exportado de Excel. Se reconocen columnas como
        <code class="text-xs bg-surface-muted px-1 rounded">descripción, cantidad, categoría, pagado por, lugar, fecha, notas</code>
        (también en inglés), importes tipo
        <code class="text-xs bg-surface-muted px-1 rounded">1.528,00 €</code> y fechas
        <code class="text-xs bg-surface-muted px-1 rounded">dd/mm/aaaa</code> o
        <code class="text-xs bg-surface-muted px-1 rounded">10 febrero 2026</code>. Las filas sin fecha
        heredan la de la fila anterior, y el lugar se guarda en las notas. Primero verás una
        previsualización; no se importa nada hasta que confirmes.
      </p>
      <UploadButton
        label="Elegir fichero CSV"
        icon="pi pi-upload"
        accept=".csv,text/csv"
        :loading="loading"
        @file="onFileChosen"
      />
    </div>

    <div v-else class="flex flex-col gap-4">
      <div class="flex items-center gap-3 flex-wrap">
        <Tag :value="`${preview.valid_rows.length} filas válidas`" severity="success" />
        <Tag
          v-if="preview.errors.length"
          :value="`${preview.errors.length} filas con errores`"
          severity="danger"
        />
        <Button
          label="Elegir otro fichero"
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
            Fila {{ err.row }}: {{ err.error }}
          </li>
          <li v-if="preview.errors.length > 8">… y {{ preview.errors.length - 8 }} más</li>
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
        <Column header="Fecha">
          <template #body="{ data }">{{ formatDate(data.day) }}</template>
        </Column>
        <Column field="category" header="Categoría" />
        <Column field="description" header="Descripción" />
        <Column header="Importe">
          <template #body="{ data }">{{ formatMoney(data.amount, data.currency) }}</template>
        </Column>
        <Column :header="`En ${trip.base_currency}`">
          <template #body="{ data }">{{ formatMoney(data.amount_base, trip.base_currency) }}</template>
        </Column>
        <Column field="paid_by" header="Pagado por" />
        <Column field="place" header="Sitio" />
        <Column field="notes" header="Notas" />
      </DataTable>
    </div>

    <template #footer>
      <Button label="Cancelar" severity="secondary" text @click="visible = false" />
      <Button
        v-if="preview"
        :label="`Importar ${preview.valid_rows.length} gastos`"
        icon="pi pi-check"
        :disabled="!preview.valid_rows.length"
        :loading="importing"
        @click="confirmImport"
      />
    </template>
  </Dialog>
</template>
