<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import Textarea from 'primevue/textarea'
import FormDialog from '../ui/FormDialog.vue'
import FormField from '../ui/FormField.vue'
import type { TripLink } from '../../api/types'
import { useLinksStore } from '../../stores/links'
import { useLinkGroupsStore } from '../../stores/linkGroups'
import { useFormDialog } from '../../composables/useFormDialog'

const props = defineProps<{
  link: TripLink | null
  /** bloque preseleccionado al crear ("Añadir enlace aquí"); null = sin bloque */
  defaultGroupId?: number | null
}>()
const visible = defineModel<boolean>('visible', { required: true })
const { t } = useI18n()
const store = useLinksStore()
const groups = useLinkGroupsStore()

// 0 = "sin bloque": el Select de PrimeVue pinta null como vacío, no como opción
const NO_GROUP = 0

const title = ref('')
const url = ref('')
const groupId = ref<number>(NO_GROUP)
const notes = ref('')

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
  },
  validate() {
    if (!title.value.trim()) return t('links.dialog.titleRequired')
    if (!url.value.trim()) return t('links.dialog.urlRequired')
    return null
  },
  submit() {
    const payload = {
      title: title.value.trim(),
      url: url.value.trim(),
      group_id: groupId.value || null,
      notes: notes.value.trim() || null,
    }
    return props.link ? store.update(props.link.id, payload) : store.create(payload)
  },
})
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
  </FormDialog>
</template>
