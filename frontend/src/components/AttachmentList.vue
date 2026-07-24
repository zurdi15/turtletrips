<script setup lang="ts">
import { computed, ref } from 'vue'
import Button from 'primevue/button'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import { useAttachmentsStore } from '../stores/attachments'

const props = defineProps<{ bookingId?: number | null }>()
const store = useAttachmentsStore()
const confirm = useConfirm()
const toast = useToast()
const fileInput = ref<HTMLInputElement>()
const uploading = ref(false)

const items = computed(() =>
  props.bookingId != null
    ? store.items.filter((a) => a.booking_id === props.bookingId)
    : store.items,
)

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

async function onFileChosen(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  uploading.value = true
  try {
    await store.upload(file, props.bookingId)
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error al subir', detail: String(err), life: 5000 })
  } finally {
    uploading.value = false
    target.value = ''
  }
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
    <div class="flex flex-wrap gap-2">
      <div
        v-for="att in items"
        :key="att.id"
        class="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-sm"
      >
        <i :class="fileIcon(att.content_type)" />
        <a
          :href="store.downloadUrl(att.id, true)"
          target="_blank"
          rel="noopener"
          class="text-slate-700 hover:text-sky-600 hover:underline max-w-[16rem] truncate"
          :title="att.original_name"
        >
          {{ att.original_name }}
        </a>
        <span class="text-xs text-slate-400">{{ formatSize(att.size_bytes) }}</span>
        <a :href="store.downloadUrl(att.id)" download>
          <Button icon="pi pi-download" text size="small" severity="secondary" />
        </a>
        <Button
          icon="pi pi-times"
          text
          size="small"
          severity="danger"
          @click="remove(att.id, att.original_name)"
        />
      </div>
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
