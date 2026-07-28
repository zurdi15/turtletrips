<script lang="ts">
/** pagador de un gasto o reserva: un viajero, el fondo común o nadie */
export type PayerValue = number | 'common' | null
/** en filtros y edición en bloque hacen falta dos centinelas más */
export type PayerFilterValue = PayerValue | 'all' | 'none'
</script>

<script setup lang="ts" generic="T extends PayerFilterValue">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import Select from 'primevue/select'
import PayerTag from './PayerTag.vue'
import type { Traveler } from '../api/types'

export interface PayerOption {
  value: PayerFilterValue
  label: string
  color?: string | null
  avatarUrl?: string | null
  muted?: boolean
}

// Selector de pagador ÚNICO de la app: mismas opciones (viajeros con su avatar,
// fondo común y los centinelas que pida el contexto) en el formulario de gasto,
// el de reserva, los filtros y la edición en bloque.
const props = withDefaults(
  defineProps<{
    travelers: Traveler[]
    /**
     * primera opción: 'unassigned' (null, formularios) o 'all' (filtros).
     * null = ninguna, y entonces el select arranca en su placeholder.
     */
    lead?: 'unassigned' | 'all' | null
    /** añade "Sin asignar" ('none') al final: filtrar o dejar sin pagador */
    includeNone?: boolean
    placeholder?: string
    disabled?: boolean
  }>(),
  { lead: 'unassigned', includeNone: false, placeholder: undefined, disabled: false },
)

const model = defineModel<T>({ required: true })
const { t } = useI18n()

const options = computed<PayerOption[]>(() => [
  ...(props.lead === 'unassigned'
    ? [{ value: null, label: t('common.payer.unassigned'), muted: true }]
    : props.lead === 'all'
      ? [{ value: 'all' as const, label: t('common.payer.anyPayer') }]
      : []),
  ...props.travelers.map((tr) => ({
    value: tr.id,
    label: tr.name,
    color: tr.color,
    avatarUrl: tr.avatar_url,
  })),
  { value: 'common' as const, label: t('common.payer.commonFund') },
  ...(props.includeNone
    ? [{ value: 'none' as const, label: t('common.payer.unassigned'), muted: true }]
    : []),
])

/**
 * Etiqueta a pintar como valor. Un valor sin opción (sin pagador, o alguien que
 * ya no viaja) cae en la cabecera "Sin asignar" en vez de dejar un dot de color
 * sin nombre; sin cabecera (edición en bloque) se enseña el placeholder.
 */
function displayed(value: PayerFilterValue | undefined): PayerOption | null {
  const found = options.value.find((o) => o.value === (value ?? null))
  if (found) return found
  return props.lead === 'unassigned' ? options.value[0] : null
}
</script>

<template>
  <Select
    v-model="model"
    :options="options"
    optionLabel="label"
    optionValue="value"
    :placeholder="placeholder"
    :disabled="disabled"
  >
    <template #option="{ option }">
      <PayerTag v-bind="option" />
    </template>
    <template #value="{ value, placeholder: emptyLabel }">
      <PayerTag v-if="displayed(value)" v-bind="displayed(value)!" />
      <template v-else>{{ emptyLabel }}</template>
    </template>
  </Select>
</template>
