<script setup lang="ts">
import InputNumber from 'primevue/inputnumber'

// contador − n +: los botones cubren el caso normal (2-5 unidades) y el número
// se puede escribir para los grandes (20 calcetines)
const props = withDefaults(
  defineProps<{
    /** nombre accesible del grupo ("Cantidad") */
    label: string
    min?: number
    max?: number
    size?: 'small'
  }>(),
  { min: 1, max: 99, size: undefined },
)
const model = defineModel<number>({ required: true })

// InputNumber emite null al vaciar el campo: se vuelve al mínimo, nunca a null
function update(value: number | null) {
  model.value = Math.min(props.max, Math.max(props.min, value ?? props.min))
}
</script>

<template>
  <InputNumber
    :modelValue="model"
    showButtons
    buttonLayout="horizontal"
    incrementButtonIcon="pi pi-plus"
    decrementButtonIcon="pi pi-minus"
    :min="min"
    :max="max"
    :size="size"
    :allowEmpty="false"
    :aria-label="label"
    :inputClass="size === 'small' ? 'tt-qty-input tt-qty-input-sm' : 'tt-qty-input'"
    class="tt-qty"
    @update:modelValue="update"
  />
</template>
