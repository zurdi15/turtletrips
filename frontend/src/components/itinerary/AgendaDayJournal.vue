<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Textarea from 'primevue/textarea'
import ImageFramer from '../ui/ImageFramer.vue'
import ImageZoom from '../ui/ImageZoom.vue'
import UploadButton from '../ui/UploadButton.vue'
import type { Focus } from '../../utils/imageFocus'
import { focusStyle } from '../../utils/imageFocus'
import { useItineraryJournalStore } from '../../stores/itineraryJournal'
import { useNotify } from '../../composables/useNotify'
import { useConfirmDelete } from '../../composables/useConfirmDelete'

// diario (texto libre autoguardado) + postal (una foto) al pie de cada día de
// la agenda; con contenido se muestra en modo lectura (texto íntegro con la
// postal ladeada a su derecha) y expandir pasa a modo edición
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

// --- encuadre de la postal ---
// La miniatura del modo lectura va recortada; aquí se elige por dónde. El
// arrastre es local y se persiste al soltar, no en cada píxel.
const photoFocus = ref<Focus>({ x: 0.5, y: 0.5 })
/** contenedor del marco: es el origen del vuelo del zoom en modo edición */
const framerBox = ref<HTMLElement | null>(null)

watch(
  () => [entry.value?.photo_url, entry.value?.photo_focus_x, entry.value?.photo_focus_y],
  () => {
    photoFocus.value = {
      x: entry.value?.photo_focus_x ?? 0.5,
      y: entry.value?.photo_focus_y ?? 0.5,
    }
  },
  { immediate: true },
)

async function saveFocus() {
  const current = entry.value
  if (!current) return
  if (current.photo_focus_x === photoFocus.value.x && current.photo_focus_y === photoFocus.value.y)
    return // dirty-check: un clic sin arrastre no manda nada
  try {
    await store.saveFocus(props.day, photoFocus.value.x, photoFocus.value.y)
  } catch (err) {
    notify.error(t('common.image.frameError'), err)
  }
}

// el zoom de la postal (vuelo FLIP desde la miniatura) vive en ImageZoom: se
// abre desde la miniatura en modo lectura y desde el marco de encuadre al editar
const zoom = ref<InstanceType<typeof ImageZoom> | null>(null)

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
      <span v-if="!expanded && !hasContent" class="text-xs text-ink-disabled truncate">
        {{ t('itinerary.journal.empty') }}
      </span>
      <i
        class="pi shrink-0 ml-auto text-ink-faint text-xs"
        :class="expanded ? 'pi-chevron-up' : hasContent ? 'pi-pencil' : 'pi-chevron-down'"
      />
    </button>

    <!-- modo lectura: texto sin truncar con la postal (marco de papel ladeado) a la derecha -->
    <div v-if="!expanded && hasContent" class="px-4 pb-4 flex items-start gap-4">
      <p
        v-if="entry?.text"
        class="flex-1 min-w-0 text-sm text-ink-secondary leading-relaxed whitespace-pre-line break-words"
      >
        {{ entry.text }}
      </p>
      <!-- blanco stock a propósito: papel de postal, invariante al modo oscuro -->
      <button
        v-if="entry?.photo_url"
        type="button"
        class="ml-auto shrink-0 w-32 sm:w-44 rotate-1 rounded bg-white p-0.5 shadow-lift flex cursor-zoom-in"
        @click="zoom?.openFrom($event.currentTarget as HTMLElement)"
      >
        <img
          :src="entry.photo_url"
          :alt="t('itinerary.journal.postcard')"
          loading="lazy"
          class="block w-full h-24 sm:h-32 rounded-sm object-cover"
          :style="{ objectPosition: focusStyle(entry.photo_focus_x, entry.photo_focus_y) }"
        />
      </button>
    </div>

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
        <div v-if="entry?.photo_url" ref="framerBox" class="flex flex-col items-start gap-2">
          <!-- se encuadra con el mismo recorte que luego luce en la agenda; para
               verla entera está el zoom -->
          <ImageFramer
            v-model="photoFocus"
            :src="entry.photo_url"
            aspect="4 / 3"
            :hint="t('common.image.frameHint')"
            class="w-48 sm:w-64"
            @pointerup="saveFocus"
            @keyup="saveFocus"
          />
          <div class="flex items-center gap-2">
            <!-- el marco enseña el recorte: para ver la foto entera, el zoom -->
            <Button
              :label="t('itinerary.journal.viewPhoto')"
              icon="pi pi-search-plus"
              severity="secondary"
              text
              size="small"
              @click="zoom?.openFrom(framerBox)"
            />
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

    <ImageZoom
      ref="zoom"
      :src="entry?.photo_url ?? null"
      :alt="t('itinerary.journal.postcard')"
    />
  </div>
</template>
