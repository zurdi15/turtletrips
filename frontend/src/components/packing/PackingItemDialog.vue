<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import FormDialog from '../ui/FormDialog.vue'
import FormField from '../ui/FormField.vue'
import type { PackingItem } from '../../api/types'
import { usePackingStore } from '../../stores/packing'
import { useFormDialog } from '../../composables/useFormDialog'

const props = defineProps<{
  item: PackingItem | null
  categoryOptions: { value: string; label: string }[]
  /** maletas a las que se puede mover el elemento (null = común) */
  bagOptions: { value: number | null; label: string }[]
}>()
const visible = defineModel<boolean>('visible', { required: true })

const store = usePackingStore()
const { t } = useI18n()

const name = ref('')
const category = ref('')
const url = ref('')
const traveler = ref<number | null>(null)

const { saving, save } = useFormDialog({
  visible,
  entity: () => props.item,
  reset(item) {
    name.value = item?.name ?? ''
    category.value = item?.category ?? ''
    url.value = item?.url ?? ''
    traveler.value = item?.traveler_id ?? null
  },
  validate: () => (name.value.trim() ? null : t('packing.itemDialog.nameRequired')),
  submit() {
    return store.update(props.item!.id, {
      name: name.value.trim(),
      category: category.value,
      url: url.value.trim() || null,
      traveler_id: traveler.value,
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
    <FormField :label="t('packing.itemDialog.name')" required>
      <InputText v-model="name" />
    </FormField>
    <div class="grid grid-cols-2 gap-3">
      <FormField :label="t('packing.itemDialog.category')">
        <Select
          v-model="category"
          :options="categoryOptions"
          optionLabel="label"
          optionValue="value"
        />
      </FormField>
      <FormField :label="t('packing.itemDialog.bag')">
        <Select v-model="traveler" :options="bagOptions" optionLabel="label" optionValue="value" />
      </FormField>
    </div>
    <FormField :label="t('packing.purchaseLink')">
      <InputText v-model="url" placeholder="https://…" />
    </FormField>
  </FormDialog>
</template>
