<script setup lang="ts">
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Tag from 'primevue/tag'
import EntityLink from '../trip/EntityLink.vue'
import type { Attachment } from '../../api/types'
import { useAttachmentsStore } from '../../stores/attachments'
import { formatDate } from '../../composables/useMoney'
import { useMediaQuery } from '../../composables/useMediaQuery'
import { fileIcon, formatSize } from '../../utils/files'

// Una sección de la pestaña Ficheros (documentación del viaje o recibos de
// gastos): tabla en escritorio y, en móvil, tarjetas con cada dato en su
// fila — como la lista de gastos — para no obligar a hacer scroll lateral.
const props = defineProps<{
  items: Attachment[]
  kind: 'trip' | 'receipts'
  tripId: number
  bookingTitle: Map<number, string>
  expenseDesc: Map<number, string>
  /** adjunto enlazado desde un gasto: se enciende */
  highlightId: number | null
}>()
defineEmits<{ remove: [id: number, name: string] }>()

const store = useAttachmentsStore()
const isDesktop = useMediaQuery('(min-width: 640px)')

function rowClass(row: Attachment): string {
  return row.id === props.highlightId ? 'tt-row-flash' : ''
}
</script>

<template>
  <!-- escritorio: tabla -->
  <DataTable
    v-if="isDesktop"
    :value="items"
    size="small"
    stripedRows
    :rowClass="rowClass"
    :tableStyle="{ minWidth: '560px' }"
    class="bg-surface rounded-card overflow-hidden border border-line"
  >
    <Column :header="$t('bookings.files.columns.file')">
      <template #body="{ data }">
        <div class="flex items-center gap-2">
          <i :class="fileIcon(data.content_type)" />
          <a
            :href="store.downloadUrl(data.id, true)"
            target="_blank"
            rel="noopener"
            class="text-ink hover:text-info hover:underline"
          >
            {{ data.original_name }}
          </a>
        </div>
      </template>
    </Column>
    <Column
      :header="kind === 'trip' ? $t('bookings.files.columns.booking') : $t('bookings.files.columns.expense')"
      style="width: 16rem"
    >
      <template #body="{ data }">
        <template v-if="kind === 'trip'">
          <Tag
            v-if="data.booking_id && bookingTitle.get(data.booking_id)"
            :value="bookingTitle.get(data.booking_id)"
            severity="secondary"
          />
          <span v-else class="text-xs text-ink-faint">{{ $t('bookings.files.tripLevel') }}</span>
        </template>
        <span v-else class="flex items-center gap-2 min-w-0">
          <EntityLink type="expense" :tripId="tripId" :targetId="data.expense_id!" />
          <span class="text-sm text-ink-muted truncate">
            {{ expenseDesc.get(data.expense_id!) ?? '—' }}
          </span>
        </span>
      </template>
    </Column>
    <Column :header="$t('bookings.files.columns.size')" style="width: 6rem">
      <template #body="{ data }">
        <span class="text-sm text-ink-muted">{{ formatSize(data.size_bytes) }}</span>
      </template>
    </Column>
    <Column :header="$t('bookings.files.columns.uploaded')" style="width: 8rem">
      <template #body="{ data }">
        <span class="text-sm text-ink-muted">{{ formatDate(data.created_at) }}</span>
      </template>
    </Column>
    <Column style="width: 6rem">
      <template #body="{ data }">
        <div class="flex gap-1 justify-end">
          <a :href="store.downloadUrl(data.id)" download>
            <Button icon="pi pi-download" text size="small" severity="secondary" />
          </a>
          <Button
            icon="pi pi-trash"
            text
            size="small"
            severity="danger"
            @click="$emit('remove', data.id, data.original_name)"
          />
        </div>
      </template>
    </Column>
  </DataTable>

  <!-- móvil: una tarjeta por fichero, cada dato en su línea -->
  <div v-else class="tt-stagger flex flex-col gap-2">
    <div
      v-for="att in items"
      :key="att.id"
      class="bg-surface rounded-card border border-line p-3 transition-colors duration-500"
      :class="rowClass(att)"
    >
      <div class="flex items-start gap-2">
        <i :class="fileIcon(att.content_type)" class="mt-0.5 shrink-0" />
        <a
          :href="store.downloadUrl(att.id, true)"
          target="_blank"
          rel="noopener"
          class="flex-1 min-w-0 text-sm font-medium text-ink break-words hover:text-info hover:underline"
        >
          {{ att.original_name }}
        </a>
        <div class="flex gap-1 -mt-1.5 -mr-1.5 shrink-0">
          <a :href="store.downloadUrl(att.id)" download>
            <Button icon="pi pi-download" text size="small" severity="secondary" />
          </a>
          <Button
            icon="pi pi-trash"
            text
            size="small"
            severity="danger"
            @click="$emit('remove', att.id, att.original_name)"
          />
        </div>
      </div>
      <dl class="mt-2 flex flex-col gap-1 text-xs">
        <div class="flex items-center gap-2 min-w-0">
          <dt class="text-ink-faint w-16 shrink-0">
            {{ kind === 'trip' ? $t('bookings.files.columns.booking') : $t('bookings.files.columns.expense') }}
          </dt>
          <dd class="min-w-0 flex items-center gap-2">
            <template v-if="kind === 'trip'">
              <Tag
                v-if="att.booking_id && bookingTitle.get(att.booking_id)"
                :value="bookingTitle.get(att.booking_id)"
                severity="secondary"
              />
              <span v-else class="text-ink-faint">{{ $t('bookings.files.tripLevel') }}</span>
            </template>
            <template v-else>
              <EntityLink type="expense" :tripId="tripId" :targetId="att.expense_id!" />
              <span class="text-ink-muted truncate">{{ expenseDesc.get(att.expense_id!) ?? '—' }}</span>
            </template>
          </dd>
        </div>
        <div class="flex items-center gap-2">
          <dt class="text-ink-faint w-16 shrink-0">{{ $t('bookings.files.columns.size') }}</dt>
          <dd class="text-ink-muted">{{ formatSize(att.size_bytes) }}</dd>
        </div>
        <div class="flex items-center gap-2">
          <dt class="text-ink-faint w-16 shrink-0">{{ $t('bookings.files.columns.uploaded') }}</dt>
          <dd class="text-ink-muted">{{ formatDate(att.created_at) }}</dd>
        </div>
      </dl>
    </div>
  </div>
</template>

<style scoped>
/* adjunto enlazado desde un gasto: se enciende y se apaga suave al limpiar */
:deep(.p-datatable-tbody > tr > td) {
  transition: background-color var(--tt-dur-600) ease;
}
:deep(.p-datatable-tbody > tr.tt-row-flash > td),
.tt-row-flash {
  background: color-mix(in srgb, var(--p-primary-color) 14%, transparent) !important;
}
</style>
