<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import UploadButton from './ui/UploadButton.vue'
import { useAttachmentsStore } from '../stores/attachments'
import { useConfirmDelete } from '../composables/useConfirmDelete'
import { useNotify } from '../composables/useNotify'
import { fileIcon, formatSize } from '../utils/files'

const props = withDefaults(
  defineProps<{ bookingId?: number | null; expenseId?: number | null; showList?: boolean }>(),
  { showList: true },
)
const store = useAttachmentsStore()
const confirmAction = useConfirmDelete()
const notify = useNotify()
const { t } = useI18n()
const uploading = ref(false)

const items = computed(() => {
  if (props.bookingId != null) return store.items.filter((a) => a.booking_id === props.bookingId)
  if (props.expenseId != null) return store.items.filter((a) => a.expense_id === props.expenseId)
  return store.items
})

async function onFileChosen(file: File) {
  uploading.value = true
  try {
    await store.upload(file, props.bookingId, props.expenseId)
  } catch (err) {
    notify.error(t('common.attachments.uploadError'), err)
  } finally {
    uploading.value = false
  }
}

function remove(id: number, name: string) {
  confirmAction({
    message: t('common.attachments.deleteConfirm', { name }),
    header: t('common.attachments.deleteHeader'),
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
          class="flex items-center gap-2 w-full bg-surface-soft border border-line rounded-lg px-2.5 py-1.5 text-sm"
        >
          <i :class="fileIcon(att.content_type)" class="shrink-0" />
          <a
            :href="store.downloadUrl(att.id, true)"
            target="_blank"
            rel="noopener"
            class="flex-1 min-w-0 truncate text-ink hover:text-info hover:underline"
            :title="att.original_name"
          >
            {{ att.original_name }}
          </a>
          <span class="text-xs text-ink-faint shrink-0">{{ formatSize(att.size_bytes) }}</span>
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
      <UploadButton
        :label="$t('common.attachments.attach')"
        icon="pi pi-paperclip"
        severity="secondary"
        outlined
        size="small"
        accept="application/pdf,image/*"
        :loading="uploading"
        @file="onFileChosen"
      />
    </div>
  </div>
</template>
