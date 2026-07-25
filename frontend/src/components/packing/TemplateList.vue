<script setup lang="ts">
import { ref } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import type { PackingTemplate } from '../../api/types'

defineProps<{ templates: PackingTemplate[]; selectedId: number | null; loading: boolean }>()
const emit = defineEmits<{ select: [id: number]; create: [name: string] }>()

const newName = ref('')

function create() {
  const name = newName.value.trim()
  if (!name) return
  emit('create', name)
  newName.value = ''
}
</script>

<template>
  <div class="bg-surface rounded-card border border-line p-4">
    <ul class="tt-stagger flex flex-col gap-1 mb-4">
      <li v-for="template in templates" :key="template.id">
        <button
          class="w-full text-left px-3 py-2 rounded-lg flex items-center gap-2 transition-colors"
          :class="
            selectedId === template.id
              ? 'bg-surface-muted text-ink-strong font-medium'
              : 'text-ink-secondary hover:bg-surface-hover'
          "
          @click="$emit('select', template.id)"
        >
          <i class="pi pi-briefcase text-xs text-ink-faint" />
          <span class="flex-1">{{ template.name }}</span>
          <span class="text-xs text-ink-faint">{{ template.item_count }}</span>
        </button>
      </li>
      <li v-if="!templates.length && !loading" class="text-sm text-ink-faint px-3 py-2">
        {{ $t('packing.templates.empty') }}
      </li>
    </ul>
    <div class="flex gap-2">
      <InputText
        v-model="newName"
        :placeholder="$t('packing.templates.newPlaceholder')"
        class="flex-1"
        size="small"
        @keyup.enter="create"
      />
      <Button icon="pi pi-plus" size="small" @click="create" />
    </div>
  </div>
</template>
