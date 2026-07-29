<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import TripDatePicker from '../ui/TripDatePicker.vue'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import FormDialog from '../ui/FormDialog.vue'
import FormField from '../ui/FormField.vue'
import type { ChecklistItem } from '../../api/types'
import { useChecklistStore } from '../../stores/checklist'
import { useTripsStore } from '../../stores/trips'
import { useFormDialog } from '../../composables/useFormDialog'
import { parseIsoDate, toIsoDate } from '../../composables/useMoney'

const props = defineProps<{ item: ChecklistItem | null }>()
const visible = defineModel<boolean>('visible', { required: true })
const { t } = useI18n()
const store = useChecklistStore()
// el viaje en curso: sus fechas sitúan el vencimiento respecto al viaje
const trip = computed(() => useTripsStore().current)

const title = ref('')
const due = ref<Date | null>(null)
const url = ref('')
const notes = ref('')

const { saving, save } = useFormDialog<ChecklistItem>({
  visible,
  entity: () => props.item,
  reset(item) {
    title.value = item?.title ?? ''
    due.value = item?.due_date ? parseIsoDate(item.due_date) : null
    url.value = item?.url ?? ''
    notes.value = item?.notes ?? ''
  },
  validate: () => (title.value.trim() ? null : t('checklist.dialog.titleRequired')),
  submit() {
    const payload = {
      title: title.value.trim(),
      due_date: due.value ? toIsoDate(due.value) : null,
      url: url.value.trim() || null,
      notes: notes.value.trim() || null,
    }
    return props.item ? store.update(props.item.id, payload) : store.create(payload)
  },
})
</script>

<template>
  <FormDialog
    v-model:visible="visible"
    :header="item ? $t('checklist.dialog.editTitle') : $t('checklist.dialog.newTitle')"
    :saving="saving"
    width="md"
    @save="save"
  >
    <FormField :label="$t('checklist.dialog.title')" required>
      <InputText v-model="title" autofocus @keyup.enter="save" />
    </FormField>
    <FormField :label="$t('checklist.dialog.due')">
      <TripDatePicker
        v-model="due"
        :tripStart="trip?.start_date"
        :tripEnd="trip?.end_date"
        showIcon
        dateFormat="dd/mm/yy"
        showButtonBar
      />
    </FormField>
    <FormField :label="$t('checklist.dialog.url')">
      <InputText v-model="url" type="url" placeholder="https://…" />
    </FormField>
    <FormField :label="$t('checklist.dialog.notes')">
      <Textarea v-model="notes" rows="2" autoResize />
    </FormField>
  </FormDialog>
</template>
