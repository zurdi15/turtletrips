<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import AttachmentList from '../../components/AttachmentList.vue'
import EmptyState from '../../components/EmptyState.vue'
import TabSkeleton from '../../components/TabSkeleton.vue'
import type { Trip } from '../../api/types'
import { useAttachmentsStore } from '../../stores/attachments'
import { useBookingsStore } from '../../stores/bookings'
import { formatDate } from '../../composables/useMoney'
import { useConfirmDelete } from '../../composables/useConfirmDelete'
import { useTripTabData } from '../../composables/useTripTabData'
import { fileIcon, formatSize } from '../../utils/files'

const props = defineProps<{ trip: Trip }>()
const { t } = useI18n()
const store = useAttachmentsStore()
const bookings = useBookingsStore()
const confirmAction = useConfirmDelete()

useTripTabData(() => props.trip, {
  load(tripId) {
    store.load(tripId)
    bookings.load(tripId)
  },
})

const bookingTitle = computed(() => new Map(bookings.items.map((b) => [b.id, b.title])))

function remove(id: number, name: string) {
  confirmAction({
    message: t('bookings.files.confirmDelete.message', { name }),
    header: t('bookings.files.confirmDelete.header'),
    accept: () => store.remove(id),
  })
}
</script>

<template>
  <div>
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

    <DataTable
      :value="store.items"
      size="small"
      stripedRows
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
    </template>
  </div>
</template>
