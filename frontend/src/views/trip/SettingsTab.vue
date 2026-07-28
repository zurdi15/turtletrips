<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import Button from 'primevue/button'
import TripForm from '../../components/trips/TripForm.vue'
import ShareTripDialog from '../../components/trip/ShareTripDialog.vue'
import type { Trip } from '../../api/types'
import { useTripsStore } from '../../stores/trips'
import { useConfirmDelete } from '../../composables/useConfirmDelete'
import { useNotify } from '../../composables/useNotify'

const props = defineProps<{ trip: Trip }>()

const { t } = useI18n()
const router = useRouter()
const store = useTripsStore()
const notify = useNotify()
const confirmAction = useConfirmDelete()

const formRef = ref<InstanceType<typeof TripForm> | null>(null)
const saving = ref(false)
const showShare = ref(false)

async function save() {
  const problem = formRef.value?.validate()
  if (problem) {
    notify.warn(problem)
    return
  }
  saving.value = true
  try {
    await formRef.value!.submit()
    notify.success(t('trips.toast.updated'))
  } catch (err) {
    notify.error(t('trips.toast.saveError'), err)
  } finally {
    saving.value = false
  }
}

function removeTrip() {
  confirmAction({
    message: t('trips.settings.confirmDelete', { name: props.trip.name }),
    header: t('trips.settings.deleteTrip'),
    accept: async () => {
      await store.deleteTrip(props.trip.id)
      notify.success(t('trips.toast.deleted'))
      router.push('/')
    },
  })
}
</script>

<template>
  <div class="max-w-3xl mx-auto flex flex-col gap-6">
    <section class="bg-surface rounded-card border border-line p-4 sm:p-6">
      <h3 class="text-sm font-semibold text-ink-secondary mb-4">
        {{ t('trips.settings.dataTitle') }}
      </h3>
      <TripForm ref="formRef" :key="trip.id" :trip="trip" />
      <div class="flex justify-end mt-5">
        <Button :label="t('trips.settings.saveChanges')" icon="pi pi-check" :loading="saving" @click="save" />
      </div>
    </section>

    <section class="bg-surface rounded-card border border-line p-4 sm:p-6">
      <div class="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 class="text-sm font-semibold text-ink-secondary mb-1">{{ t('share.section.title') }}</h3>
          <p class="text-sm text-ink-muted">
            {{ trip.share_token ? t('share.section.active') : t('share.section.inactive') }}
          </p>
        </div>
        <Button
          :label="trip.share_token ? t('share.section.manage') : t('share.section.share')"
          icon="pi pi-share-alt"
          :outlined="!!trip.share_token"
          severity="secondary"
          @click="showShare = true"
        />
      </div>
    </section>

    <!-- rojos stock: los tonos danger son invariantes al modo -->
    <section class="rounded-card border border-red-500/40 p-4 sm:p-6">
      <h3 class="text-sm font-semibold text-red-600 mb-1">{{ t('trips.settings.dangerZone') }}</h3>
      <p class="text-sm text-ink-muted mb-4">
        {{ t('trips.settings.dangerHint') }}
      </p>
      <Button
        :label="t('trips.settings.deleteTrip')"
        icon="pi pi-trash"
        severity="danger"
        outlined
        @click="removeTrip"
      />
    </section>

    <ShareTripDialog v-model:visible="showShare" :trip="trip" />
  </div>
</template>
