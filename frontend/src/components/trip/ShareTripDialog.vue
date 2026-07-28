<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import Checkbox from 'primevue/checkbox'
import Message from 'primevue/message'
import { api } from '../../api/client'
import type { ShareScope, ShareState, Trip } from '../../api/types'
import { useNotify } from '../../composables/useNotify'
import { useConfirmDelete } from '../../composables/useConfirmDelete'
import { useTripsStore } from '../../stores/trips'

const props = defineProps<{ trip: Trip }>()
const visible = defineModel<boolean>('visible', { required: true })

const { t } = useI18n()
const notify = useNotify()
const trips = useTripsStore()
const confirmAction = useConfirmDelete()
const working = ref(false)

const SCOPES: ShareScope[] = ['itinerary', 'bookings', 'map']
const scopes = ref<ShareScope[]>([])

// al abrir, el estado sale del viaje (TripRead ya trae token y scopes). Un
// viaje sin compartir llega con la lista VACÍA, no nula: sin este length el
// diálogo se abriría con todo desmarcado y crearía un enlace que no enseña nada
watch(
  visible,
  (open) => {
    if (open) scopes.value = props.trip.share_scopes?.length ? [...props.trip.share_scopes] : [...SCOPES]
  },
  { immediate: true },
)

const url = computed(() =>
  props.trip.share_token ? `${window.location.origin}/s/${props.trip.share_token}` : null,
)

async function run(call: () => Promise<unknown>, errorKey: string) {
  working.value = true
  try {
    await call()
    await trips.loadTrip(props.trip.id)
  } catch (err) {
    notify.error(t(errorKey), err)
  } finally {
    working.value = false
  }
}

function share() {
  return run(
    () => api.put<ShareState>(`/trips/${props.trip.id}/share`, { scopes: scopes.value }),
    'share.dialog.saveError',
  )
}

function rotate() {
  confirmAction({
    message: t('share.dialog.confirmRotate'),
    header: t('share.dialog.rotate'),
    acceptLabel: t('share.dialog.rotate'),
    accept: () =>
      run(
        () => api.post<ShareState>(`/trips/${props.trip.id}/share/rotate`, {}),
        'share.dialog.saveError',
      ),
  })
}

function stop() {
  confirmAction({
    message: t('share.dialog.confirmStop'),
    header: t('share.dialog.stop'),
    acceptLabel: t('share.dialog.stop'),
    accept: () =>
      run(() => api.delete(`/trips/${props.trip.id}/share`), 'share.dialog.saveError'),
  })
}

function copy() {
  if (!url.value) return
  navigator.clipboard?.writeText(url.value)
  notify.info(t('share.dialog.copied'))
}
</script>

<template>
  <Dialog
    v-model:visible="visible"
    modal
    :header="t('share.dialog.title')"
    class="w-full max-w-lg mx-4"
  >
    <div class="flex flex-col gap-4 text-sm text-ink-secondary">
      <p>{{ t('share.dialog.intro') }}</p>

      <div class="flex flex-col gap-2">
        <span class="text-xs font-medium text-ink-muted uppercase tracking-wide">
          {{ t('share.dialog.sections') }}
        </span>
        <label
          v-for="scope in SCOPES"
          :key="scope"
          class="flex items-center gap-2 cursor-pointer"
        >
          <Checkbox v-model="scopes" :value="scope" :inputId="`scope-${scope}`" />
          <span>{{ t(`share.scopes.${scope}`) }}</span>
        </label>
      </div>

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
            v-tooltip.top="t('share.dialog.copyTooltip')"
            @click="copy"
          />
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <Button
            :label="t('share.dialog.save')"
            icon="pi pi-check"
            size="small"
            :loading="working"
            @click="share"
          />
          <Button
            :label="t('share.dialog.rotate')"
            icon="pi pi-refresh"
            text
            size="small"
            severity="secondary"
            v-tooltip.top="t('share.dialog.rotateTooltip')"
            @click="rotate"
          />
          <Button
            :label="t('share.dialog.stop')"
            icon="pi pi-times-circle"
            text
            size="small"
            severity="danger"
            class="ml-auto"
            @click="stop"
          />
        </div>
      </template>
      <Button
        v-else
        :label="t('share.dialog.start')"
        icon="pi pi-share-alt"
        class="w-fit"
        :loading="working"
        @click="share"
      />

      <Message severity="warn" size="small">{{ t('share.dialog.privacy') }}</Message>
    </div>
  </Dialog>
</template>
