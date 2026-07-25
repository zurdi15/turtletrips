<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import Button from 'primevue/button'
import Checkbox from 'primevue/checkbox'
import InputNumber from 'primevue/inputnumber'
import ClusterBtn from './ui/ClusterBtn.vue'
import type { SplitMode, Traveler } from '../api/types'
import { equalSplit, splitRemaining, sumValues } from '../composables/useSplit'
import { formatMoney } from '../composables/useMoney'

export interface SplitState {
  split_mode: SplitMode
  shares: { traveler_id: number; value: number | null }[]
}

const props = defineProps<{
  travelers: Traveler[]
  amount: number | null
  currency: string
}>()

const model = defineModel<SplitState>({ required: true })

const expanded = ref(false)

// al abrir el diálogo con un reparto personalizado, mostrarlo desplegado
watch(
  () => model.value,
  (v) => {
    expanded.value = v.shares.length > 0
  },
)

const modeOptions = [
  { value: 'equal', label: 'Partes iguales', icon: 'pi pi-equals' },
  { value: 'amount', label: 'Importes', icon: 'pi pi-money-bill' },
  { value: 'percent', label: 'Porcentajes', icon: 'pi pi-percentage' },
] as const

const mode = computed({
  get: () => model.value.split_mode,
  set: (m: SplitMode) => {
    model.value.split_mode = m
    prefillValues(m)
  },
})

const isCustomValues = computed(() => mode.value !== 'equal')

function prefillValues(m: SplitMode) {
  const shares = model.value.shares
  if (m === 'equal') {
    for (const s of shares) s.value = null
    return
  }
  const total = m === 'amount' ? (props.amount ?? 0) : 100
  const parts = equalSplit(total, shares.length)
  shares.forEach((s, i) => {
    s.value = parts[i]
  })
}

function customize() {
  if (!model.value.shares.length) {
    model.value.shares = props.travelers.map((t) => ({ traveler_id: t.id, value: null }))
  }
  expanded.value = true
}

function reset() {
  model.value.split_mode = 'equal'
  model.value.shares = []
  expanded.value = false
}

function isChecked(travelerId: number): boolean {
  return model.value.shares.some((s) => s.traveler_id === travelerId)
}

function toggle(travelerId: number) {
  const shares = model.value.shares
  const idx = shares.findIndex((s) => s.traveler_id === travelerId)
  if (idx >= 0) shares.splice(idx, 1)
  else shares.push({ traveler_id: travelerId, value: null })
}

function valueOf(travelerId: number): number | null {
  return model.value.shares.find((s) => s.traveler_id === travelerId)?.value ?? null
}

function setValue(travelerId: number, value: number | null) {
  const share = model.value.shares.find((s) => s.traveler_id === travelerId)
  if (share) share.value = value
}

const summary = computed(() => {
  const shares = model.value.shares
  if (!shares.length) return 'entre todos a partes iguales'
  if (mode.value === 'equal') return `entre ${shares.length} a partes iguales`
  return `personalizado (${shares.length} participantes)`
})

const expectedTotal = computed(() =>
  mode.value === 'amount' ? (props.amount ?? 0) : 100,
)
const currentSum = computed(() => sumValues(model.value.shares.map((s) => s.value)))
const pending = computed(
  () => Math.round((expectedTotal.value - currentSum.value) * 100) / 100,
)

function fillRemaining() {
  const values = splitRemaining(
    expectedTotal.value,
    model.value.shares.map((s) => s.value),
  )
  model.value.shares.forEach((s, i) => {
    s.value = values[i]
  })
}

function fmt(v: number): string {
  return mode.value === 'amount' ? formatMoney(v, props.currency) : `${v}%`
}
</script>

<template>
  <div class="rounded-lg bg-surface-soft border border-line p-3">
    <div class="flex items-center gap-2">
      <span class="text-sm text-ink-secondary">
        <i class="pi pi-users text-xs mr-1" />Reparto: {{ summary }}
      </span>
      <span class="flex-1" />
      <Button
        v-if="!expanded"
        label="Personalizar"
        size="small"
        text
        :disabled="!travelers.length"
        @click="customize"
      />
      <Button v-else label="Restablecer" size="small" text severity="secondary" @click="reset" />
    </div>
    <p v-if="!travelers.length" class="text-xs text-ink-faint mt-1">
      Añade viajeros al viaje para repartir el gasto.
    </p>

    <div v-if="expanded" class="mt-3 flex flex-col gap-3">
      <ClusterBtn v-model="mode" :options="modeOptions" size="small" />
      <div class="flex flex-col gap-1.5">
        <div v-for="t in travelers" :key="t.id" class="flex items-center gap-2.5">
          <Checkbox
            :modelValue="isChecked(t.id)"
            binary
            :inputId="`split-${t.id}`"
            @update:modelValue="toggle(t.id)"
          />
          <label :for="`split-${t.id}`" class="text-sm text-ink flex-1 cursor-pointer">
            {{ t.name }}
          </label>
          <InputNumber
            v-if="isCustomValues && isChecked(t.id)"
            :modelValue="valueOf(t.id)"
            :minFractionDigits="0"
            :maxFractionDigits="2"
            locale="es-ES"
            :min="0"
            :suffix="mode === 'percent' ? ' %' : undefined"
            inputClass="w-24 text-right"
            @update:modelValue="(v) => setValue(t.id, v)"
          />
        </div>
      </div>
      <div v-if="isCustomValues" class="flex items-center gap-2 text-xs">
        <span :class="pending === 0 ? 'text-brand' : 'text-warn'">
          Suman {{ fmt(currentSum) }} de {{ fmt(expectedTotal) }}
          <template v-if="pending !== 0"> — faltan {{ fmt(pending) }}</template>
        </span>
        <span class="flex-1" />
        <Button
          v-if="pending !== 0"
          label="Repartir el resto"
          size="small"
          text
          @click="fillRemaining"
        />
      </div>
    </div>
  </div>
</template>
