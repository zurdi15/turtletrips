<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import InputText from 'primevue/inputtext'
import FormDialog from '../ui/FormDialog.vue'
import FormField from '../ui/FormField.vue'
import type { Attachment } from '../../api/types'
import { useAttachmentsStore } from '../../stores/attachments'
import { useFormDialog } from '../../composables/useFormDialog'
import { fileExtension } from '../../utils/files'

// Renombrar un fichero subido: cambia el nombre que se ve y con el que se
// descarga, no el fichero en disco. La extensión la conserva el servidor si
// no se escribe, así que aquí solo se avisa.
const props = defineProps<{ file: Attachment | null }>()
const visible = defineModel<boolean>('visible', { required: true })

const store = useAttachmentsStore()
const { t } = useI18n()

const name = ref('')
const extension = computed(() => fileExtension(props.file?.original_name ?? ''))

const { saving, save } = useFormDialog<Attachment>({
  visible,
  entity: () => props.file,
  reset(file) {
    name.value = file?.original_name ?? ''
  },
  validate: () => (name.value.trim() ? null : t('bookings.files.rename.nameRequired')),
  submit: () => store.update(props.file!.id, { original_name: name.value.trim() }),
})
</script>

<template>
  <FormDialog
    v-model:visible="visible"
    :header="t('bookings.files.rename.title')"
    width="md"
    :saving="saving"
    @save="save"
  >
    <FormField :label="t('bookings.files.rename.name')" required>
      <InputText v-model="name" autofocus @keyup.enter="save" />
      <template v-if="extension" #hint>
        <p class="text-xs text-ink-faint">
          {{ t('bookings.files.rename.keepsExtension', { ext: extension }) }}
        </p>
      </template>
    </FormField>
  </FormDialog>
</template>
