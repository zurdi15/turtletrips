<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import QuantityStepper from '../ui/QuantityStepper.vue'
import PackingCategorySelect from './PackingCategorySelect.vue'

export interface PackingAddPayload {
  name: string
  category: string
  url: string | null
  quantity: number
}

const props = withDefaults(
  defineProps<{
    placeholder: string
    defaultCategory?: string
    /** función-prop: el componente espera la promesa y limpia su estado solo
     *  si tuvo éxito (si lanza, el texto se conserva y el padre notifica) */
    onAdd: (payload: PackingAddPayload) => Promise<void>
  }>(),
  { defaultCategory: 'Ropa' },
)
const { t } = useI18n()

const name = ref('')
const category = ref(props.defaultCategory)
const quantity = ref(1)
const url = ref('')
const showUrlField = ref(false)

async function add() {
  const trimmed = name.value.trim()
  if (!trimmed) return
  await props.onAdd({
    name: trimmed,
    category: category.value,
    url: url.value.trim() || null,
    quantity: quantity.value,
  })
  // la categoría se queda (se suelen apuntar varias cosas de la misma); la
  // cantidad vuelve a 1, que lo normal es llevar una
  name.value = ''
  quantity.value = 1
  url.value = ''
  showUrlField.value = false
}
</script>

<template>
  <div class="flex flex-wrap items-center gap-2">
    <InputText v-model="name" :placeholder="placeholder" class="w-full sm:w-56" @keyup.enter="add" />
    <QuantityStepper v-model="quantity" :label="t('packing.quantity')" class="shrink-0" />
    <PackingCategorySelect v-model="category" class="flex-1 min-w-0 sm:flex-none sm:w-44" />
    <Button
      icon="pi pi-link"
      severity="secondary"
      :outlined="!showUrlField"
      v-tooltip.top="t('packing.addBar.linkTooltip')"
      @click="showUrlField = !showUrlField"
    />
    <InputText
      v-if="showUrlField"
      v-model="url"
      :placeholder="t('packing.addBar.urlPlaceholder')"
      class="w-full sm:w-56"
      @keyup.enter="add"
    />
    <Button
      :label="t('common.actions.add')"
      icon="pi pi-plus"
      class="shrink-0 max-sm:[&_.p-button-label]:hidden"
      @click="add"
    />
  </div>
</template>
