<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import TravelerAvatar from '../ui/TravelerAvatar.vue'
import UploadButton from '../ui/UploadButton.vue'
import FileRenameDialog from '../files/FileRenameDialog.vue'
import type { Document, Traveler } from '../../api/types'
import { useDocumentsStore } from '../../stores/documents'
import { useConfirmDelete } from '../../composables/useConfirmDelete'
import { useNotify } from '../../composables/useNotify'
import { formatDate } from '../../composables/useMoney'
import { fileIcon, formatSize } from '../../utils/files'

// Documentos personales de la familia (DNI, pasaporte, carnet…): uno por
// viajero, incluidos los que no tienen cuenta. Los ve y los gestiona toda la
// familia — quien compra los vuelos necesita el pasaporte de todos.
const props = defineProps<{ members: Traveler[] }>()

const store = useDocumentsStore()
const confirmAction = useConfirmDelete()
const notify = useNotify()
const { t } = useI18n()

onMounted(() => store.load(true).catch(() => {}))

const byTraveler = computed(() => {
  const map = new Map<number, Document[]>()
  for (const doc of store.items) map.set(doc.traveler_id, [...(map.get(doc.traveler_id) ?? []), doc])
  return map
})

const busyFor = ref<number | null>(null)

async function upload(file: File, travelerId: number) {
  busyFor.value = travelerId
  try {
    await store.upload(file, travelerId)
  } catch (err) {
    notify.error(t('family.documents.uploadError'), err)
  } finally {
    busyFor.value = null
  }
}

const renaming = ref<Document | null>(null)
const showRename = ref(false)

function openRename(doc: Document) {
  renaming.value = doc
  showRename.value = true
}

function remove(doc: Document) {
  confirmAction({
    message: t('family.documents.confirmDelete.message', { name: doc.original_name }),
    header: t('family.documents.confirmDelete.header'),
    accept: () => store.remove(doc.id),
  })
}
</script>

<template>
  <section class="bg-surface rounded-card border border-line p-4">
    <div class="flex items-center gap-2 mb-1 px-3">
      <i class="text-sm pi pi-id-card" />
      <h2 class="flex-1 font-semibold text-ink">{{ t('family.documents.title') }}</h2>
      <span class="text-2xs text-ink-faint">{{ store.items.length }}</span>
    </div>
    <p class="text-xs text-ink-faint px-3 mb-3">{{ t('family.documents.hint') }}</p>

    <ul class="flex flex-col gap-3">
      <li v-for="member in members" :key="member.id" class="rounded-lg bg-surface-soft p-3">
        <div class="flex items-center gap-2">
          <TravelerAvatar
            :name="member.name"
            :color="member.color"
            :avatar-url="member.avatar_url"
            :focus-x="member.avatar_focus_x"
            :focus-y="member.avatar_focus_y"
            size="xs"
          />
          <span class="flex-1 text-sm font-medium text-ink truncate">{{ member.name }}</span>
          <UploadButton
            :label="t('family.documents.add')"
            icon="pi pi-paperclip"
            severity="secondary"
            outlined
            size="small"
            accept="application/pdf,image/*"
            :loading="busyFor === member.id"
            class="shrink-0 max-sm:[&_.p-button-label]:hidden"
            @file="(file: File) => upload(file, member.id)"
          />
        </div>

        <ul v-if="byTraveler.get(member.id)?.length" class="mt-2 flex flex-col gap-1">
          <li
            v-for="doc in byTraveler.get(member.id)"
            :key="doc.id"
            class="flex items-center gap-2 rounded-lg bg-surface border border-line-subtle px-2.5 py-1.5"
          >
            <i :class="fileIcon(doc.content_type)" class="shrink-0" />
            <a
              :href="store.downloadUrl(doc.id, true)"
              target="_blank"
              rel="noopener"
              class="flex-1 min-w-0 text-sm text-ink break-words hover:text-info hover:underline"
            >
              {{ doc.original_name }}
            </a>
            <span class="hidden sm:inline text-2xs text-ink-faint shrink-0">
              {{ formatSize(doc.size_bytes) }} · {{ formatDate(doc.created_at) }}
            </span>
            <span class="flex shrink-0 -mr-1.5">
              <Button
                icon="pi pi-pencil"
                text
                size="small"
                severity="secondary"
                :aria-label="t('bookings.files.rename.action')"
                @click="openRename(doc)"
              />
              <a :href="store.downloadUrl(doc.id)" download>
                <Button icon="pi pi-download" text size="small" severity="secondary" />
              </a>
              <Button
                icon="pi pi-trash"
                text
                size="small"
                severity="danger"
                @click="remove(doc)"
              />
            </span>
          </li>
        </ul>
        <p v-else class="mt-2 text-xs text-ink-faint">{{ t('family.documents.empty') }}</p>
      </li>
    </ul>

    <FileRenameDialog
      v-model:visible="showRename"
      :file="renaming"
      :onRename="(name: string) => store.update(renaming!.id, { original_name: name })"
    />
  </section>
</template>
