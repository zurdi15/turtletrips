<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import { FALLBACK_CATEGORY_COLOR, useCategoriesStore } from '../../stores/categories'
import { useNotify } from '../../composables/useNotify'
import { CATEGORY_PALETTE } from '../../theme'

// selector de categoría de maleta con "Nueva categoría" como primera opción:
// elegirla cambia el selector por un campo de nombre y la categoría se crea
// en el acto (Intro o ✓), así sirve igual en la barra de añadir, en el diálogo
// y en la edición inline de la plantilla
defineProps<{ size?: 'small' }>()
const model = defineModel<string>({ required: true })

const categories = useCategoriesStore()
const notify = useNotify()
const { t } = useI18n()

// -1 = "nueva categoría": las categorías de verdad son nombres (strings)
const NEW_CATEGORY = -1

const options = computed(() => [
  { value: NEW_CATEGORY, label: t('packing.categorySelect.new'), color: null },
  ...categories.packing.map((c) => ({
    value: c.name,
    label: c.name,
    color: c.color ?? FALLBACK_CATEGORY_COLOR,
  })),
])
const selected = computed(() => options.value.find((o) => o.value === model.value) ?? null)

// "Nueva categoría" va la primera y con un filete debajo: es una acción, no una
// categoría más (mismo patrón que "Nuevo bloque" en el diálogo de enlaces)
const selectPt = {
  option: ({ context }: { context: { option?: { value: string | number } } }) =>
    context.option?.value === NEW_CATEGORY
      ? {
          class:
            "relative mb-2 !overflow-visible !text-primary after:content-[''] after:absolute after:-inset-x-1 after:-bottom-1 after:border-b after:border-line",
        }
      : {},
}

const creating = ref(false)
const saving = ref(false)
const newName = ref('')
const nameInput = ref<{ $el: HTMLInputElement } | null>(null)

function pick(value: string | number) {
  if (value !== NEW_CATEGORY) {
    model.value = value as string
    return
  }
  newName.value = ''
  creating.value = true
  // autofocus no vale en un campo que aparece después, y el Select se queda el
  // foco al cerrarse
  nextTick(() => setTimeout(() => nameInput.value?.$el.focus()))
}

async function create() {
  const name = newName.value.trim()
  if (!name || saving.value) return
  // si ya existe (en otra capitalización) se elige esa en vez de chocar con el 409
  const existing = categories.packing.find((c) => c.name.toLowerCase() === name.toLowerCase())
  if (existing) {
    model.value = existing.name
    creating.value = false
    return
  }
  saving.value = true
  try {
    // color de la paleta por turno, como al crearla desde Ajustes (se cambia allí)
    const color = CATEGORY_PALETTE[categories.packing.length % CATEGORY_PALETTE.length]
    const category = await categories.create('packing', name, color)
    model.value = category.name
    creating.value = false
  } catch (err) {
    notify.error(t('packing.categorySelect.createError'), err)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div v-if="creating" class="relative flex items-center min-w-0">
    <InputText
      ref="nameInput"
      v-model="newName"
      :size="size"
      :placeholder="t('packing.categorySelect.namePlaceholder')"
      :aria-label="t('packing.categorySelect.namePlaceholder')"
      class="w-full min-w-0 !pr-16"
      @keydown.enter.prevent.stop="create"
      @keydown.esc.prevent.stop="creating = false"
    />
    <span class="absolute right-0.5 flex">
      <Button
        icon="pi pi-check"
        text
        rounded
        size="small"
        :loading="saving"
        :disabled="!newName.trim()"
        :aria-label="t('packing.categorySelect.create')"
        v-tooltip.top="t('packing.categorySelect.create')"
        @click="create"
      />
      <Button
        icon="pi pi-times"
        text
        rounded
        size="small"
        severity="secondary"
        :aria-label="t('common.actions.cancel')"
        @click="creating = false"
      />
    </span>
  </div>
  <Select
    v-else
    :modelValue="model"
    :options="options"
    optionLabel="label"
    optionValue="value"
    :size="size"
    :pt="selectPt"
    @update:modelValue="pick"
  >
    <template #option="{ option }">
      <span class="flex items-center gap-2 min-w-0">
        <i v-if="option.value === NEW_CATEGORY" class="pi pi-plus-circle" />
        <span v-else class="w-2.5 h-2.5 rounded-full shrink-0" :style="{ background: option.color }" />
        <span class="truncate">{{ option.label }}</span>
      </span>
    </template>
    <template #value="{ placeholder }">
      <span v-if="selected" class="flex items-center gap-2 min-w-0">
        <span class="w-2.5 h-2.5 rounded-full shrink-0" :style="{ background: selected.color ?? undefined }" />
        <span class="truncate">{{ selected.label }}</span>
      </span>
      <!-- categoría huérfana (borrada en Ajustes): se enseña tal cual -->
      <span v-else-if="model" class="truncate">{{ model }}</span>
      <span v-else>{{ placeholder || '&nbsp;' }}</span>
    </template>
  </Select>
</template>
