<script setup lang="ts">
import { computed, ref } from 'vue'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import Message from 'primevue/message'
import { api } from '../api/client'
import { useNotify } from '../composables/useNotify'
import type { Trip } from '../api/types'
import { useTripsStore } from '../stores/trips'

const props = defineProps<{ trip: Trip }>()
const visible = defineModel<boolean>('visible', { required: true })

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
    notify.error('Error al generar el enlace', err)
  } finally {
    working.value = false
  }
}

function copy() {
  if (!url.value) return
  navigator.clipboard?.writeText(url.value)
  notify.info('Enlace copiado')
}
</script>

<template>
  <Dialog
    v-model:visible="visible"
    modal
    header="Suscribirse al calendario"
    class="w-full max-w-lg mx-4"
  >
    <div class="flex flex-col gap-4 text-sm text-ink-secondary">
      <p>
        Suscríbete desde tu calendario y el itinerario se actualizará solo, sin volver a
        importar: en Google Calendar ve a
        <span class="font-medium">Otros calendarios → + → Desde URL</span> y pega este enlace.
      </p>

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
            v-tooltip.top="'Copiar enlace'"
            @click="copy"
          />
        </div>
        <Button
          label="Regenerar enlace"
          icon="pi pi-refresh"
          text
          size="small"
          class="w-fit"
          :loading="working"
          v-tooltip.right="'El enlace anterior dejará de funcionar'"
          @click="rotate"
        />
      </template>
      <Button
        v-else
        label="Generar enlace de suscripción"
        icon="pi pi-link"
        class="w-fit"
        :loading="working"
        @click="rotate"
      />

      <Message severity="info" size="small">
        El enlace lleva un token secreto y tiene que ser accesible desde internet sin
        autenticación: si tu reverse proxy protege la app, excluye la ruta
        <span class="font-mono">/api/v1/calendar/</span>. Google refresca las suscripciones
        cada varias horas (no es instantáneo).
      </Message>
    </div>
  </Dialog>
</template>
