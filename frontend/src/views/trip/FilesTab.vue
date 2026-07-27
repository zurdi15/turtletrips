<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import AttachmentList from '../../components/AttachmentList.vue'
import EmptyState from '../../components/EmptyState.vue'
import EntityLink from '../../components/trip/EntityLink.vue'
import TabSkeleton from '../../components/TabSkeleton.vue'
import type { Trip } from '../../api/types'
import { useAttachmentsStore } from '../../stores/attachments'
import { useBookingsStore } from '../../stores/bookings'
import { useExpensesStore } from '../../stores/expenses'
import { formatDate } from '../../composables/useMoney'
import { useConfirmDelete } from '../../composables/useConfirmDelete'
import { useRowFlash } from '../../composables/useRowFlash'
import { useTripTabData } from '../../composables/useTripTabData'
import { fileIcon, formatSize } from '../../utils/files'

const props = defineProps<{ trip: Trip }>()
const { t } = useI18n()
const store = useAttachmentsStore()
const bookings = useBookingsStore()
const expenses = useExpensesStore()
const confirmAction = useConfirmDelete()

const route = useRoute()
// llegar desde un gasto (?attachment=id) enciende ese adjunto
const highlightId = ref<number | null>(null)

useTripTabData(() => props.trip, {
  load(tripId) {
    store.load(tripId)
    bookings.load(tripId)
    expenses.load(tripId)
  },
  afterFirstLoad() {
    const fromQuery = Number(route.query.attachment)
    if (fromQuery) {
      highlightId.value = fromQuery
      setTimeout(() => (highlightId.value = null), 4000)
    }
  },
})

const rootEl = ref<HTMLElement | null>(null)
// sin paginación en estas tablas: pageRows alto deja el salto de página en no-op
const first = ref(0)
const pageRows = ref(10000)
const { rowClass } = useRowFlash({
  rows: () => store.items,
  highlightId: () => highlightId.value,
  first,
  pageRows,
  root: () => rootEl.value,
})

const bookingTitle = computed(() => new Map(bookings.items.map((b) => [b.id, b.title])))
const expenseDesc = computed(() => new Map(expenses.items.map((e) => [e.id, e.description])))

// los recibos de gastos van en su propia sección (conceptualmente aparte
// de la documentación del viaje: billetes, visados…)
const receipts = computed(() => store.items.filter((a) => a.expense_id != null))
const tripFiles = computed(() => store.items.filter((a) => a.expense_id == null))

function remove(id: number, name: string) {
  confirmAction({
    message: t('bookings.files.confirmDelete.message', { name }),
    header: t('bookings.files.confirmDelete.header'),
    accept: () => store.remove(id),
  })
}
</script>

<template>
  <div ref="rootEl">
    <TabSkeleton v-if="store.loading && !store.items.length" variant="table" :rows="4" />

    <!-- vacío: un único mensaje con el botón de adjuntar como acción -->
    <EmptyState
      v-else-if="!store.items.length"
      icon="pi pi-paperclip"
      :title="$t('bookings.files.empty.title')"
      :subtitle="$t('bookings.files.empty.subtitle')"
    >
      <AttachmentList :show-list="false" />
    </EmptyState>

    <template v-else>
    <div class="mb-4">
      <p class="text-sm text-ink-muted mb-3">
        {{ $t('bookings.files.intro') }}
      </p>
      <AttachmentList :show-list="false" />
    </div>

    <!-- documentación del viaje (billetes, visados, adjuntos de reservas…) -->
    <h3 v-if="tripFiles.length && receipts.length" class="text-sm font-semibold text-ink-secondary mb-2">
      {{ $t('bookings.files.sections.trip') }}
    </h3>
    <DataTable
      v-if="tripFiles.length"
      :value="tripFiles"
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
      <Column :header="$t('bookings.files.columns.booking')" style="width: 16rem">
        <template #body="{ data }">
          <Tag
            v-if="data.booking_id && bookingTitle.get(data.booking_id)"
            :value="bookingTitle.get(data.booking_id)"
            severity="secondary"
          />
          <span v-else class="text-xs text-ink-faint">{{ $t('bookings.files.tripLevel') }}</span>
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
              @click="remove(data.id, data.original_name)"
            />
          </div>
        </template>
      </Column>
    </DataTable>

    <!-- recibos de gastos: sección propia, con enlace al gasto -->
    <template v-if="receipts.length">
      <h3 class="text-sm font-semibold text-ink-secondary mb-2" :class="tripFiles.length ? 'mt-5' : ''">
        {{ $t('bookings.files.sections.receipts') }}
      </h3>
      <DataTable
        :value="receipts"
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
        <Column :header="$t('bookings.files.columns.expense')" style="width: 16rem">
          <template #body="{ data }">
            <span class="flex items-center gap-2 min-w-0">
              <EntityLink type="expense" :tripId="trip.id" :targetId="data.expense_id" />
              <span class="text-sm text-ink-muted truncate">
                {{ expenseDesc.get(data.expense_id) ?? '—' }}
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
                @click="remove(data.id, data.original_name)"
              />
            </div>
          </template>
        </Column>
      </DataTable>
    </template>
    </template>
  </div>
</template>

<style scoped>
/* adjunto enlazado desde un gasto: se enciende y se apaga suave al limpiar */
:deep(.p-datatable-tbody > tr > td) {
  transition: background-color var(--tt-dur-600) ease;
}
:deep(.p-datatable-tbody > tr.tt-row-flash > td) {
  background: color-mix(in srgb, var(--p-primary-color) 14%, transparent) !important;
}
</style>
