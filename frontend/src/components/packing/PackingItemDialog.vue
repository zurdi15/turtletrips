<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import FormDialog from '../ui/FormDialog.vue'
import FormField from '../ui/FormField.vue'
import QuantityStepper from '../ui/QuantityStepper.vue'
import PackingCategorySelect from './PackingCategorySelect.vue'
import type { PackingItem } from '../../api/types'
import { usePackingStore } from '../../stores/packing'
import { useFormDialog } from '../../composables/useFormDialog'

const props = defineProps<{
  item: PackingItem | null
  /** maletas a las que se puede mover el elemento (null = común) */
  bagOptions: { value: number | null; label: string }[]
}>()
const visible = defineModel<boolean>('visible', { required: true })

const store = usePackingStore()
const { t } = useI18n()

// 0 = maleta común: el Select de PrimeVue pinta null como vacío, no como opción
const COMMON_BAG = 0
const bagSelectOptions = computed(() =>
  props.bagOptions.map((b) => ({ value: b.value ?? COMMON_BAG, label: b.label })),
)

const name = ref('')
const category = ref('')
const quantity = ref(1)
const url = ref('')
const traveler = ref<number>(COMMON_BAG)

const { saving, save } = useFormDialog({
  visible,
  entity: () => props.item,
  reset(item) {
    name.value = item?.name ?? ''
    category.value = item?.category ?? ''
    quantity.value = item?.quantity ?? 1
    url.value = item?.url ?? ''
    traveler.value = item?.traveler_id ?? COMMON_BAG
  },
  validate: () => (name.value.trim() ? null : t('packing.itemDialog.nameRequired')),
  submit() {
    return store.update(props.item!.id, {
      name: name.value.trim(),
      category: category.value,
      quantity: quantity.value,
      url: url.value.trim() || null,
      traveler_id: traveler.value || null,
    })
  },
})
</script>

<template>
  <FormDialog
    v-model:visible="visible"
    :header="t('packing.itemDialog.title')"
    width="md"
    :saving="saving"
    @save="save"
  >
    <div class="grid grid-cols-[1fr_auto] gap-3">
      <FormField :label="t('packing.itemDialog.name')" required>
        <InputText v-model="name" />
      </FormField>
      <FormField :label="t('packing.quantity')">
        <QuantityStepper v-model="quantity" :label="t('packing.quantity')" class="!w-auto" />
      </FormField>
    </div>
    <div class="grid grid-cols-2 gap-3">
      <FormField :label="t('packing.itemDialog.category')">
        <PackingCategorySelect v-model="category" />
      </FormField>
      <FormField :label="t('packing.itemDialog.bag')">
        <Select
          v-model="traveler"
          :options="bagSelectOptions"
          optionLabel="label"
          optionValue="value"
        />
      </FormField>
    </div>
    <FormField :label="t('packing.purchaseLink')">
      <InputText v-model="url" placeholder="https://…" />
    </FormField>
  </FormDialog>
</template>
