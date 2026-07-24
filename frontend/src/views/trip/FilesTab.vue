<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import { useConfirm } from 'primevue/useconfirm'
import AttachmentList from '../../components/AttachmentList.vue'
import EmptyState from '../../components/EmptyState.vue'
import type { Trip } from '../../api/types'
import { useAttachmentsStore } from '../../stores/attachments'
import { useBookingsStore } from '../../stores/bookings'
import { formatDate } from '../../composables/useMoney'

const props = defineProps<{ trip: Trip }>()
const store = useAttachmentsStore()
const bookings = useBookingsStore()
const confirm = useConfirm()

function loadAll(tripId: number) {
  store.load(tripId)
  bookings.load(tripId)
}
onMounted(() => loadAll(props.trip.id))
watch(() => props.trip.id, loadAll)

const bookingTitle = computed(() => new Map(bookings.items.map((b) => [b.id, b.title])))

function fileIcon(contentType: string): string {
  if (contentType === 'application/pdf') return 'pi pi-file-pdf text-red-500'
  if (contentType.startsWith('image/')) return 'pi pi-image text-sky-500'
  return 'pi pi-file text-slate-400'
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

function remove(id: number, name: string) {
  confirm.require({
    message: `¿Eliminar el fichero "${name}"?`,
    header: 'Eliminar adjunto',
    icon: 'pi pi-exclamation-triangle',
    rejectProps: { label: 'Cancelar', severity: 'secondary', outlined: true },
    acceptProps: { label: 'Eliminar', severity: 'danger' },
    accept: () => store.remove(id),
  })
}
</script>

<template>
  <div>
    <div class="mb-4">
      <p class="text-sm text-slate-500 mb-3">
        Ficheros del viaje (billetes, seguros, documentación…). Los adjuntos de reservas también
        aparecen aquí.
      </p>
      <AttachmentList v-if="!store.items.length" />
    </div>

    <EmptyState
      v-if="!store.loading && !store.items.length"
      icon="pi pi-paperclip"
      title="Sin ficheros"
      subtitle="Sube PDFs de reservas, billetes o cualquier documento del viaje"
    />

    <DataTable
      v-else
      :value="store.items"
      size="small"
      stripedRows
      :tableStyle="{ minWidth: '560px' }"
      class="bg-white rounded-xl overflow-hidden border border-slate-200"
    >
      <Column header="Fichero">
        <template #body="{ data }">
          <div class="flex items-center gap-2">
            <i :class="fileIcon(data.content_type)" />
            <a
              :href="store.downloadUrl(data.id, true)"
              target="_blank"
              rel="noopener"
              class="text-slate-700 hover:text-sky-600 hover:underline"
            >
              {{ data.original_name }}
            </a>
          </div>
        </template>
      </Column>
      <Column header="Reserva" style="width: 16rem">
        <template #body="{ data }">
          <Tag
            v-if="data.booking_id && bookingTitle.get(data.booking_id)"
            :value="bookingTitle.get(data.booking_id)"
            severity="secondary"
          />
          <span v-else class="text-xs text-slate-400">Nivel de viaje</span>
        </template>
      </Column>
      <Column header="Tamaño" style="width: 6rem">
        <template #body="{ data }">
          <span class="text-sm text-slate-500">{{ formatSize(data.size_bytes) }}</span>
        </template>
      </Column>
      <Column header="Subido" style="width: 8rem">
        <template #body="{ data }">
          <span class="text-sm text-slate-500">{{ formatDate(data.created_at) }}</span>
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

    <div v-if="store.items.length" class="mt-4">
      <AttachmentList />
    </div>
  </div>
</template>
