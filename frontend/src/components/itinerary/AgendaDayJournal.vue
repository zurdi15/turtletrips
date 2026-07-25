<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Textarea from 'primevue/textarea'
import UploadButton from '../ui/UploadButton.vue'
import { useItineraryJournalStore } from '../../stores/itineraryJournal'
import { useNotify } from '../../composables/useNotify'
import { useConfirmDelete } from '../../composables/useConfirmDelete'

// diario (texto libre autoguardado) + postal (una foto) al pie de cada día de
// la agenda; plegado por defecto con vista previa cuando ya hay contenido
const props = defineProps<{ tripId: number; day: string }>()

const { t } = useI18n()
const store = useItineraryJournalStore()
const notify = useNotify()
const confirmAction = useConfirmDelete()

const expanded = ref(false)
const draft = ref('')
const focused = ref(false)
const saving = ref(false)
const savedFlash = ref(false)
const uploading = ref(false)

const entry = computed(() => store.byDay.get(props.day) ?? null)
const hasContent = computed(() => !!(entry.value?.text?.trim() || entry.value?.photo_url))

// el borrador refleja el estado del store salvo mientras se está editando
watch(
  entry,
  (e) => {
    if (!focused.value) draft.value = e?.text ?? ''
  },
  { immediate: true },
)

async function onBlur() {
  focused.value = false
  const current = entry.value?.text ?? ''
  if (draft.value === current) return // dirty-check: nada que guardar, sin PUT no-op
  saving.value = true
  try {
    await store.saveText(props.day, draft.value)
    savedFlash.value = true
    setTimeout(() => (savedFlash.value = false), 2000)
  } catch (err) {
    notify.error(t('itinerary.journal.saveError'), err)
  } finally {
    saving.value = false
  }
}

async function onPhoto(file: File) {
  uploading.value = true
  try {
    await store.uploadPhoto(props.day, file)
  } catch (err) {
    notify.error(t('itinerary.journal.photoError'), err)
  } finally {
    uploading.value = false
  }
}

function confirmDeletePhoto() {
  confirmAction({
    header: t('itinerary.journal.deletePhotoConfirm.header'),
    message: t('itinerary.journal.deletePhotoConfirm.message'),
    accept: async () => {
      try {
        await store.deletePhoto(props.day)
      } catch (err) {
        notify.error(t('itinerary.journal.photoError'), err)
      }
    },
  })
}
</script>

<template>
  <div class="border-t border-line-subtle">
    <button
      type="button"
      class="flex items-center gap-2 w-full px-4 py-2.5 text-left hover:bg-surface-hover"
      @click="expanded = !expanded"
    >
      <i class="mdi mdi-notebook-outline text-ink-faint" />
      <span class="text-sm font-medium text-ink-secondary shrink-0">
        {{ t('itinerary.journal.title') }}
      </span>
      <!-- vista previa compacta solo cuando está plegado -->
      <div v-if="!expanded" class="flex items-center gap-2 flex-1 min-w-0">
        <img
          v-if="entry?.photo_url"
          :src="entry.photo_url"
          alt=""
          loading="lazy"
          class="h-6 w-6 rounded object-cover shrink-0"
        />
        <span v-if="entry?.text" class="text-xs text-ink-faint line-clamp-1">
          {{ entry.text }}
        </span>
        <span v-else-if="!hasContent" class="text-xs text-ink-disabled">
          {{ t('itinerary.journal.empty') }}
        </span>
      </div>
      <i
        class="pi shrink-0 ml-auto text-ink-faint text-xs"
        :class="expanded ? 'pi-chevron-up' : 'pi-chevron-down'"
      />
    </button>

    <div v-if="expanded" class="px-4 pb-4 pt-1 flex flex-col gap-4">
      <!-- diario: autoguardado al salir del textarea -->
      <div>
        <Textarea
          v-model="draft"
          class="w-full"
          rows="3"
          autoResize
          :placeholder="t('itinerary.journal.placeholder')"
          @focus="focused = true"
          @blur="onBlur"
        />
        <transition name="tt-fade">
          <span
            v-if="savedFlash"
            class="mt-1 inline-flex items-center gap-1 text-xs text-brand-strong"
          >
            <i class="pi pi-check text-2xs" /> {{ t('itinerary.journal.saved') }}
          </span>
        </transition>
      </div>

      <!-- postal: una foto del día -->
      <div>
        <div class="flex items-center gap-2 mb-1.5 text-xs font-medium text-ink-secondary">
          <i class="mdi mdi-postage-stamp text-ink-faint" />
          {{ t('itinerary.journal.postcard') }}
        </div>
        <div v-if="entry?.photo_url" class="flex flex-col items-start gap-2">
          <img
            :src="entry.photo_url"
            :alt="t('itinerary.journal.postcard')"
            loading="lazy"
            class="max-h-64 w-auto max-w-full rounded-card border border-line object-contain shadow-lift"
          />
          <div class="flex items-center gap-2">
            <UploadButton
              :label="t('itinerary.journal.replacePhoto')"
              icon="pi pi-image"
              severity="secondary"
              outlined
              size="small"
              accept="image/*"
              :loading="uploading"
              @file="onPhoto"
            />
            <Button
              :label="t('itinerary.journal.deletePhoto')"
              icon="pi pi-trash"
              text
              size="small"
              severity="danger"
              @click="confirmDeletePhoto"
            />
          </div>
        </div>
        <UploadButton
          v-else
          :label="t('itinerary.journal.addPhoto')"
          icon="mdi mdi-image-plus"
          severity="secondary"
          outlined
          size="small"
          accept="image/*"
          :loading="uploading"
          @file="onPhoto"
        />
      </div>
    </div>
  </div>
</template>
