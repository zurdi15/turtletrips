<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import Textarea from 'primevue/textarea'
import CoverImage from '../ui/CoverImage.vue'
import FormDialog from '../ui/FormDialog.vue'
import FormField from '../ui/FormField.vue'
import UploadButton from '../ui/UploadButton.vue'
import type { TripLink } from '../../api/types'
import { useLinksStore } from '../../stores/links'
import { useLinkGroupsStore } from '../../stores/linkGroups'
import { useFormDialog } from '../../composables/useFormDialog'
import { useNotify } from '../../composables/useNotify'

const props = defineProps<{
  link: TripLink | null
  /** bloque preseleccionado al crear ("Añadir enlace aquí"); null = sin bloque */
  defaultGroupId?: number | null
}>()
const visible = defineModel<boolean>('visible', { required: true })
const { t } = useI18n()
const notify = useNotify()
const store = useLinksStore()
const groups = useLinkGroupsStore()

// 0 = "sin bloque": el Select de PrimeVue pinta null como vacío, no como opción
const NO_GROUP = 0

const title = ref('')
const url = ref('')
const groupId = ref<number>(NO_GROUP)
const notes = ref('')

// imagen: al editar se gestiona en el acto contra el enlace (buscar en la
// web, subir a mano, quitar); al crear se deja elegida y se sube tras guardar
const imageUrl = ref<string | null>(null)
const imageBusy = ref(false)
const pendingImage = ref<File | null>(null)
const pendingPreview = computed(() =>
  pendingImage.value ? URL.createObjectURL(pendingImage.value) : null,
)

const groupOptions = computed(() => [
  { value: NO_GROUP, label: t('links.noGroup') },
  ...groups.items.map((g) => ({ value: g.id, label: g.name })),
])

const { saving, save } = useFormDialog<TripLink>({
  visible,
  entity: () => props.link,
  reset(link) {
    title.value = link?.title ?? ''
    url.value = link?.url ?? ''
    groupId.value = link ? (link.group_id ?? NO_GROUP) : (props.defaultGroupId ?? NO_GROUP)
    notes.value = link?.notes ?? ''
    imageUrl.value = link?.image_url ?? null
    pendingImage.value = null
  },
  validate() {
    if (!title.value.trim()) return t('links.dialog.titleRequired')
    if (!url.value.trim()) return t('links.dialog.urlRequired')
    return null
  },
  async submit() {
    const payload = {
      title: title.value.trim(),
      url: url.value.trim(),
      group_id: groupId.value || null,
      notes: notes.value.trim() || null,
    }
    if (props.link) return store.update(props.link.id, payload)
    const created = await store.create(payload)
    if (pendingImage.value) {
      try {
        await store.uploadImage(created.id, pendingImage.value)
      } catch (err) {
        notify.error(t('links.toast.imageError'), err)
      }
    }
    return created
  },
})

async function fetchFromWeb() {
  if (!props.link) return
  imageBusy.value = true
  try {
    const found = await store.refreshImage(props.link.id)
    imageUrl.value = store.items.find((l) => l.id === props.link!.id)?.image_url ?? null
    if (found) notify.success(t('links.toast.imageUpdated'))
    else notify.info(t('links.toast.noImage'), t('links.toast.noImageDetail'))
  } catch (err) {
    notify.error(t('links.toast.imageError'), err)
  } finally {
    imageBusy.value = false
  }
}

async function upload(file: File) {
  if (!props.link) {
    pendingImage.value = file
    return
  }
  imageBusy.value = true
  try {
    const updated = await store.uploadImage(props.link.id, file)
    imageUrl.value = updated.image_url
  } catch (err) {
    notify.error(t('links.toast.imageError'), err)
  } finally {
    imageBusy.value = false
  }
}

async function removeImage() {
  if (!props.link) {
    pendingImage.value = null
    return
  }
  imageBusy.value = true
  try {
    await store.removeImage(props.link.id)
    imageUrl.value = null
  } catch (err) {
    notify.error(t('links.toast.imageError'), err)
  } finally {
    imageBusy.value = false
  }
}
</script>

<template>
  <FormDialog
    v-model:visible="visible"
    :header="link ? $t('links.dialog.editTitle') : $t('links.dialog.newTitle')"
    :saving="saving"
    width="md"
    @save="save"
  >
    <FormField :label="$t('links.dialog.title')" required>
      <InputText v-model="title" autofocus @keyup.enter="save" />
    </FormField>
    <FormField :label="$t('links.dialog.url')" required>
      <InputText v-model="url" type="url" placeholder="https://…" @keyup.enter="save" />
    </FormField>
    <FormField v-if="groups.items.length" :label="$t('links.dialog.group')">
      <Select v-model="groupId" :options="groupOptions" optionLabel="label" optionValue="value" />
    </FormField>
    <FormField :label="$t('links.dialog.notes')">
      <Textarea v-model="notes" rows="2" autoResize />
    </FormField>

    <div class="pt-3 border-t border-line-subtle flex flex-col gap-2">
      <p class="text-sm font-medium">{{ $t('links.dialog.image') }}</p>
      <CoverImage
        v-if="imageUrl || pendingPreview"
        :src="(pendingPreview ?? imageUrl)!"
        :alt="title"
        imgClass="w-full h-full object-cover"
        class="w-full h-40 rounded-lg bg-surface-muted"
      />
      <p v-else class="text-xs text-ink-faint">{{ $t('links.dialog.imageHint') }}</p>
      <div class="flex flex-wrap gap-2">
        <!-- "buscar en la web" solo tiene sentido con el enlace ya guardado:
             es el servidor quien visita la página -->
        <Button
          v-if="link"
          :label="$t('links.dialog.fetchImage')"
          icon="pi pi-globe"
          severity="secondary"
          outlined
          size="small"
          :loading="imageBusy"
          @click="fetchFromWeb"
        />
        <UploadButton
          :label="$t('links.dialog.uploadImage')"
          icon="pi pi-image"
          severity="secondary"
          outlined
          size="small"
          accept="image/*"
          :loading="imageBusy"
          @file="upload"
        />
        <Button
          v-if="imageUrl || pendingImage"
          :label="$t('links.dialog.removeImage')"
          icon="pi pi-times"
          severity="danger"
          text
          size="small"
          :disabled="imageBusy"
          @click="removeImage"
        />
      </div>
    </div>
  </FormDialog>
</template>
