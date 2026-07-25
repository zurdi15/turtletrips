<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import Message from 'primevue/message'
import { api } from '../../api/client'
import { useNotify } from '../../composables/useNotify'
import type { Trip } from '../../api/types'
import { useTripsStore } from '../../stores/trips'

const props = defineProps<{ trip: Trip }>()
const visible = defineModel<boolean>('visible', { required: true })

const { t } = useI18n()
const notify = useNotify()
const trips = useTripsStore()
const working = ref(false)

const url = computed(() =>
  props.trip.ics_token
    ? `${window.location.origin}/api/v1/calendar/${props.trip.ics_token}.ics`
    : null,
)

async function rotate() {
  working.value = true
  try {
    await api.post(`/trips/${props.trip.id}/ics-token`, {})
    await trips.loadTrip(props.trip.id)
  } catch (err) {
    notify.error(t('itinerary.subscribe.generateError'), err)
  } finally {
    working.value = false
  }
}

function copy() {
  if (!url.value) return
  navigator.clipboard?.writeText(url.value)
  notify.info(t('itinerary.subscribe.copied'))
}
</script>

<template>
  <Dialog
    v-model:visible="visible"
    modal
    :header="t('itinerary.subscribe.title')"
    class="w-full max-w-lg mx-4"
  >
    <div class="flex flex-col gap-4 text-sm text-ink-secondary">
      <i18n-t keypath="itinerary.subscribe.intro" tag="p" scope="global">
        <template #path>
          <span class="font-medium">{{ t('itinerary.subscribe.introPath') }}</span>
        </template>
      </i18n-t>

      <template v-if="url">
        <div class="flex gap-2">
          <InputText
            :modelValue="url"
            readonly
            class="flex-1 font-mono !text-xs"
            @focus="($event.target as HTMLInputElement).select()"
          />
          <Button
            icon="pi pi-copy"
            severity="secondary"
            outlined
            v-tooltip.top="t('itinerary.subscribe.copyTooltip')"
            @click="copy"
          />
        </div>
        <Button
          :label="t('itinerary.subscribe.regenerate')"
          icon="pi pi-refresh"
          text
          size="small"
          class="w-fit"
          :loading="working"
          v-tooltip.right="t('itinerary.subscribe.regenerateTooltip')"
          @click="rotate"
        />
      </template>
      <Button
        v-else
        :label="t('itinerary.subscribe.generate')"
        icon="pi pi-link"
        class="w-fit"
        :loading="working"
        @click="rotate"
      />

      <Message severity="info" size="small">
        <i18n-t keypath="itinerary.subscribe.note" scope="global">
          <template #route>
            <span class="font-mono">/api/v1/calendar/</span>
          </template>
        </i18n-t>
      </Message>
    </div>
  </Dialog>
</template>
