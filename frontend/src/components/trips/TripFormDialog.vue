<script setup lang="ts">
import { ref } from 'vue'
import FormDialog from '../ui/FormDialog.vue'
import TripForm from './TripForm.vue'
import type { Trip } from '../../api/types'
import { useFormDialog } from '../../composables/useFormDialog'

const props = defineProps<{ trip?: Trip | null }>()
const visible = defineModel<boolean>('visible', { required: true })
const emit = defineEmits<{ saved: [trip: Trip] }>()

const formRef = ref<InstanceType<typeof TripForm> | null>(null)

const { saving, save } = useFormDialog({
  visible,
  entity: () => props.trip,
  // TripForm se monta fresco en cada apertura (v-if) y se inicializa solo
  reset: () => {},
  validate: () => formRef.value?.validate() ?? null,
  async submit() {
    const trip = await formRef.value!.submit()
    emit('saved', trip)
  },
})
</script>

<template>
  <FormDialog
    v-model:visible="visible"
    :header="trip ? $t('trips.dialog.editTitle') : $t('trips.actions.newTrip')"
    :saving="saving"
    :saveLabel="trip ? $t('common.actions.save') : $t('trips.actions.createTrip')"
    @save="save"
  >
    <TripForm v-if="visible" ref="formRef" :trip="trip" autofocus />
  </FormDialog>
</template>
