<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
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
// -1 = "nuevo bloque": abre el campo de nombre y el bloque se crea al guardar
const NEW_GROUP = -1

const title = ref('')
const url = ref('')
const groupId = ref<number>(NO_GROUP)
const newGroupName = ref('')
const notes = ref('')

// imagen: al editar se gestiona en el acto contra el enlace (buscar en la
// web, subir a mano, quitar); al crear se deja elegida y se sube tras guardar
const imageUrl = ref<string | null>(null)
const imageBusy = ref(false)
const pendingImage = ref<File | null>(null)
const pendingPreview = computed(() =>
  pendingImage.value ? URL.createObjectURL(pendingImage.value) : null,
)

// "Nuevo bloque" va el primero y con un filete debajo: es una acción, no un
// bloque más de la lista (con ! porque la opción de PrimeVue fija su color y
// su overflow: hidden, que recortaría el filete)
const groupOptions = computed(() => [
  { value: NEW_GROUP, label: t('links.newGroup'), icon: 'pi pi-folder-plus' },
  { value: NO_GROUP, label: t('links.noGroup'), icon: null },
  ...groups.items.map((g) => ({ value: g.id, label: g.name, icon: null })),
])
const groupSelectPt = {
  option: ({ context }: { context: { option?: { value: number } } }) =>
    context.option?.value === NEW_GROUP
      ? {
          class:
            "relative mb-2 !overflow-visible !text-primary after:content-[''] after:absolute after:-inset-x-1 after:-bottom-1 after:border-b after:border-line",
        }
      : {},
}

// elegir "Nuevo bloque" lleva el foco al nombre (autofocus no vale en un
// campo que aparece después; y el Select, al cerrarse, se queda el foco)
const newGroupInput = ref<{ $el: HTMLInputElement } | null>(null)
watch(groupId, (value) => {
  if (value !== NEW_GROUP) return
  nextTick(() => setTimeout(() => newGroupInput.value?.$el.focus()))
})

const { saving, save } = useFormDialog<TripLink>({
  visible,
  entity: () => props.link,
  reset(link) {
    title.value = link?.title ?? ''
    url.value = link?.url ?? ''
    groupId.value = link ? (link.group_id ?? NO_GROUP) : (props.defaultGroupId ?? NO_GROUP)
    newGroupName.value = ''
    notes.value = link?.notes ?? ''
    imageUrl.value = link?.image_url ?? null
    pendingImage.value = null
  },
  validate() {
    if (!title.value.trim()) return t('links.dialog.titleRequired')
    if (!url.value.trim()) return t('links.dialog.urlRequired')
    if (groupId.value === NEW_GROUP && !newGroupName.value.trim())
      return t('links.groupDialog.nameRequired')
    return null
  },
  async submit() {
    // el bloque nuevo se crea primero (con el icono por defecto, que se cambia
    // luego desde su cabecera) y el enlace entra ya en él. Queda elegido: si
    // falla el enlace, reintentar no crea un segundo bloque
    if (groupId.value === NEW_GROUP) {
      const group = await groups.create({ name: newGroupName.value.trim(), icon: null })
      groupId.value = group.id
    }
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
    <FormField :label="$t('links.dialog.group')">
      <Select
        v-model="groupId"
        :options="groupOptions"
        optionLabel="label"
        optionValue="value"
        :pt="groupSelectPt"
      >
        <template #option="{ option }">
          <span class="flex items-center gap-2">
            <i v-if="option.icon" :class="option.icon" />
            {{ option.label }}
          </span>
        </template>
      </Select>
      <InputText
        v-if="groupId === NEW_GROUP"
        ref="newGroupInput"
        v-model="newGroupName"
        :placeholder="$t('links.groupDialog.namePlaceholder')"
        :aria-label="$t('links.dialog.newGroupName')"
        class="mt-1"
        @keyup.enter="save"
      />
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
