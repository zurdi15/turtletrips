<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import InputText from 'primevue/inputtext'
import FormDialog from '../ui/FormDialog.vue'
import FormField from '../ui/FormField.vue'
import { useLinkGroupsStore } from '../../stores/linkGroups'
import { useFormDialog } from '../../composables/useFormDialog'

// solo crea: renombrar va inline en la cabecera del bloque
const visible = defineModel<boolean>('visible', { required: true })
const { t } = useI18n()
const store = useLinkGroupsStore()

const name = ref('')

const { saving, save } = useFormDialog<never>({
  visible,
  entity: () => null,
  reset() {
    name.value = ''
  },
  validate: () => (name.value.trim() ? null : t('links.groupDialog.nameRequired')),
  submit: () => store.create({ name: name.value.trim() }),
})
</script>

<template>
  <FormDialog
    v-model:visible="visible"
    :header="$t('links.groupDialog.newTitle')"
    :saving="saving"
    width="md"
    @save="save"
  >
    <FormField :label="$t('links.groupDialog.name')" required>
      <InputText
        v-model="name"
        autofocus
        :placeholder="$t('links.groupDialog.namePlaceholder')"
        @keyup.enter="save"
      />
    </FormField>
  </FormDialog>
</template>
