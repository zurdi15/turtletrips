<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Select from 'primevue/select'
import Textarea from 'primevue/textarea'
import { flagEmoji } from '../../countries'
import { intlLocale } from '../../i18n'
import { visitMonths, visitYears } from '../../utils/worldDates'

// Tarjeta de alta: tocar un país o una región en el mapa ya no da de alta nada,
// abre esto. Vive en el mismo hueco que `WorldCountryCard` (flota sobre el
// mapa, no es un popup de Leaflet) para que el sitio de la ficha sea siempre el
// mismo, y de paso deja poner la fecha en el momento — que a toro pasado nadie
// se acuerda de en qué año pisó un país.
export interface MarkDetails {
  visited_year: number | null
  visited_month: number | null
  note: string | null
}

const props = defineProps<{
  /** 'country' | 'region': solo cambia el rótulo del tipo */
  kind: 'country' | 'region'
  /** ISO alpha-2 del país (la bandera es la suya también en las regiones) */
  countryCode: string
  name: string
  saving: boolean
}>()

const emit = defineEmits<{ cancel: []; confirm: [details: MarkDetails] }>()

const { t } = useI18n()

const year = ref<number | null>(null)
const month = ref<number | null>(null)
const note = ref('')

// la tarjeta no se desmonta al saltar de un sitio a otro: sin esto, el año que
// pusiste en Cataluña se quedaría puesto al tocar Andalucía
watch(
  () => [props.kind, props.countryCode, props.name],
  () => {
    year.value = null
    month.value = null
    note.value = ''
  },
)

const yearOptions = computed(() => [
  { value: null as number | null, label: t('world.form.noYear') },
  ...visitYears().map((y) => ({ value: y as number | null, label: String(y) })),
])

const monthOptions = computed(() => [
  { value: null as number | null, label: '—' },
  ...visitMonths(intlLocale()).map((m) => ({ value: m.value as number | null, label: m.label })),
])

function confirm() {
  emit('confirm', {
    visited_year: year.value,
    // un mes sin año no significa nada (misma regla que el formulario completo)
    visited_month: year.value != null ? month.value : null,
    note: note.value.trim() || null,
  })
}
</script>

<template>
  <div class="tt-pop-in absolute inset-x-3 bottom-3 z-map-overlay sm:inset-x-auto sm:left-3 sm:w-72">
    <div class="bg-surface border border-line rounded-card shadow-lift p-3">
      <div class="flex items-start gap-2">
        <span class="text-2xl leading-none">{{ flagEmoji(countryCode) }}</span>
        <div class="min-w-0 flex-1">
          <div class="font-semibold text-ink truncate">{{ name }}</div>
          <div class="text-xs text-ink-muted mt-0.5">
            {{ t(`world.kind.${kind}`) }} · {{ t('world.mark.hint') }}
          </div>
        </div>
        <Button
          icon="pi pi-times"
          severity="secondary"
          text
          size="small"
          class="-mr-1.5 -mt-1.5"
          :aria-label="t('common.actions.cancel')"
          @click="$emit('cancel')"
        />
      </div>

      <div class="grid grid-cols-2 gap-2 mt-3">
        <label class="flex flex-col gap-1">
          <span class="text-2xs font-medium text-ink-muted uppercase tracking-wide">
            {{ t('world.form.visitedYear') }}
          </span>
          <Select
            v-model="year"
            :options="yearOptions"
            optionLabel="label"
            optionValue="value"
            size="small"
            filter
          />
        </label>
        <label class="flex flex-col gap-1">
          <span class="text-2xs font-medium text-ink-muted uppercase tracking-wide">
            {{ t('world.form.visitedMonth') }}
          </span>
          <Select
            v-model="month"
            :options="monthOptions"
            optionLabel="label"
            optionValue="value"
            size="small"
            :disabled="year == null"
          />
        </label>
      </div>

      <Textarea
        v-model="note"
        rows="2"
        autoResize
        class="w-full mt-2 !text-sm"
        :placeholder="t('world.form.notePlaceholder')"
      />

      <div class="flex items-center justify-end gap-2 mt-3">
        <Button
          :label="t('common.actions.cancel')"
          size="small"
          text
          severity="secondary"
          @click="$emit('cancel')"
        />
        <Button
          :label="t('common.actions.add')"
          icon="pi pi-check"
          size="small"
          :loading="saving"
          @click="confirm"
        />
      </div>
    </div>
  </div>
</template>
