<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Textarea from 'primevue/textarea'
import type { Trip } from '../../api/types'
import { useTripsStore } from '../../stores/trips'
import { useNotify } from '../../composables/useNotify'

// Notas del viaje editables en sitio desde el Resumen (el formulario del
// viaje ya no las lleva): lápiz → textarea → guardar/cancelar.
const props = defineProps<{ trip: Trip }>()
const { t } = useI18n()
const store = useTripsStore()
const notify = useNotify()

const editing = ref(false)
const draft = ref('')
const saving = ref(false)

function startEdit() {
  draft.value = props.trip.notes ?? ''
  editing.value = true
}

async function save() {
  saving.value = true
  try {
    await store.updateTrip(props.trip.id, { notes: draft.value.trim() || null })
    notify.success(t('trips.overview.notesSaved'))
    editing.value = false
  } catch (err) {
    notify.error(t('common.form.saveError'), err)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="bg-surface rounded-card border border-line p-4">
    <div class="flex items-center gap-2 mb-2">
      <h3 class="flex-1 text-sm font-semibold text-ink-secondary">
        {{ $t('trips.overview.notes') }}
      </h3>
      <template v-if="editing">
        <Button
          :label="$t('common.actions.cancel')"
          text
          size="small"
          severity="secondary"
          :disabled="saving"
          @click="editing = false"
        />
        <Button :label="$t('common.actions.save')" size="small" :loading="saving" @click="save" />
      </template>
      <Button v-else icon="pi pi-pencil" text size="small" severity="secondary" @click="startEdit" />
    </div>
    <Textarea
      v-if="editing"
      v-model="draft"
      class="w-full"
      rows="4"
      autoResize
      autofocus
      :placeholder="$t('trips.overview.notesPlaceholder')"
      @keydown.ctrl.enter="save"
      @keydown.meta.enter="save"
    />
    <p v-else-if="trip.notes" class="text-sm text-ink-secondary whitespace-pre-wrap">
      {{ trip.notes }}
    </p>
    <p v-else class="text-sm text-ink-faint">{{ $t('trips.overview.notesEmpty') }}</p>
  </div>
</template>
