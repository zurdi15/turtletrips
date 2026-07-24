<script setup lang="ts">
import { computed, ref } from 'vue'
import Button from 'primevue/button'
import { useAttachmentsStore } from '../stores/attachments'
import { useConfirmDelete } from '../composables/useConfirmDelete'
import { useNotify } from '../composables/useNotify'
import { fileIcon, formatSize } from '../utils/files'

const props = withDefaults(
  defineProps<{ bookingId?: number | null; showList?: boolean }>(),
  { showList: true },
)
const store = useAttachmentsStore()
const confirmAction = useConfirmDelete()
const notify = useNotify()
const fileInput = ref<HTMLInputElement>()
const uploading = ref(false)

const items = computed(() =>
  props.bookingId != null
    ? store.items.filter((a) => a.booking_id === props.bookingId)
    : store.items,
)

async function onFileChosen(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  uploading.value = true
  try {
    await store.upload(file, props.bookingId)
  } catch (err) {
    notify.error('Error al subir', err)
  } finally {
    uploading.value = false
    target.value = ''
  }
}

function remove(id: number, name: string) {
  confirmAction({
    message: `¿Eliminar el fichero "${name}"?`,
    header: 'Eliminar adjunto',
    accept: () => store.remove(id),
  })
}
</script>

<template>
  <div>
    <div class="flex flex-col items-start gap-2">
      <template v-if="showList">
        <div
          v-for="att in items"
          :key="att.id"
          class="flex items-center gap-2 w-full bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-sm"
        >
          <i :class="fileIcon(att.content_type)" class="shrink-0" />
          <a
            :href="store.downloadUrl(att.id, true)"
            target="_blank"
            rel="noopener"
            class="flex-1 min-w-0 truncate text-slate-700 hover:text-sky-600 hover:underline"
            :title="att.original_name"
          >
            {{ att.original_name }}
          </a>
          <span class="text-xs text-slate-400 shrink-0">{{ formatSize(att.size_bytes) }}</span>
          <a :href="store.downloadUrl(att.id)" download class="shrink-0">
            <Button icon="pi pi-download" text size="small" severity="secondary" />
          </a>
          <Button
            icon="pi pi-times"
            text
            size="small"
            severity="danger"
            class="shrink-0"
            @click="remove(att.id, att.original_name)"
          />
        </div>
      </template>
      <input
        ref="fileInput"
        type="file"
        accept="application/pdf,image/*"
        class="hidden"
        @change="onFileChosen"
      />
      <Button
        label="Adjuntar"
        icon="pi pi-paperclip"
        severity="secondary"
        outlined
        size="small"
        :loading="uploading"
        @click="fileInput?.click()"
      />
    </div>
  </div>
</template>
