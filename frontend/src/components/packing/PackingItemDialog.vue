<script setup lang="ts">
import { ref } from 'vue'
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
  validate: () => (name.value.trim() ? null : 'El nombre es obligatorio'),
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
    header="Editar elemento"
    width="md"
    :saving="saving"
    @save="save"
  >
    <FormField label="Nombre" required>
      <InputText v-model="name" />
    </FormField>
    <div class="grid grid-cols-2 gap-3">
      <FormField label="Categoría">
        <Select
          v-model="category"
          :options="categoryOptions"
          optionLabel="label"
          optionValue="value"
        />
      </FormField>
      <FormField label="Maleta de">
        <Select v-model="traveler" :options="bagOptions" optionLabel="label" optionValue="value" />
      </FormField>
    </div>
    <FormField label="Enlace de compra">
      <InputText v-model="url" placeholder="https://…" />
    </FormField>
  </FormDialog>
</template>
