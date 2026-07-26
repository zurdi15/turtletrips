<script setup lang="ts">
import { computed, ref, watchEffect } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import TravelerAvatar from '../ui/TravelerAvatar.vue'
import type { PackingTemplate } from '../../api/types'

/** Grupo de plantillas de un dueño (el usuario o un virtual de su familia) */
export interface TemplateOwnerGroup {
  ownerId: number
  name: string
  color: string | null
  avatarUrl: string | null
  isYou: boolean
  templates: PackingTemplate[]
}

export interface OwnerOption {
  value: number
  label: string
  name: string
  color: string | null
  avatarUrl: string | null
}

const props = defineProps<{
  groups: TemplateOwnerGroup[]
  /** dueños posibles al crear (el propio usuario primero) */
  ownerOptions: OwnerOption[]
  selectedId: number | null
  loading: boolean
}>()
const emit = defineEmits<{ select: [id: number]; create: [name: string, ownerId: number] }>()

const newName = ref('')
const newOwner = ref<number | null>(null)

// preselecciona "Tú" en cuanto llegan las opciones (los virtuales cargan async)
watchEffect(() => {
  if (newOwner.value === null && props.ownerOptions.length) {
    newOwner.value = props.ownerOptions[0].value
  }
})

const selectedOwner = computed(
  () => props.ownerOptions.find((o) => o.value === newOwner.value) ?? null,
)

function create() {
  const name = newName.value.trim()
  if (!name || newOwner.value === null) return
  emit('create', name, newOwner.value)
  newName.value = ''
}
</script>

<template>
  <div class="bg-surface rounded-card border border-line p-4">
    <div class="tt-stagger flex flex-col gap-3 mb-4">
      <div v-for="group in groups" :key="group.ownerId">
        <!-- cabecera del dueño: cada plantilla pertenece a un viajero -->
        <div class="flex items-center gap-2 px-1 mb-1">
          <TravelerAvatar
            :name="group.name"
            :color="group.color"
            :avatar-url="group.avatarUrl"
            size="sm"
          />
          <span class="text-sm font-semibold text-ink-heading">
            {{ group.isYou ? $t('packing.templatesView.yours') : group.name }}
          </span>
        </div>
        <ul class="flex flex-col gap-1">
          <li v-for="template in group.templates" :key="template.id">
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
        </ul>
      </div>
      <p v-if="!groups.length && !loading" class="text-sm text-ink-faint px-3 py-2">
        {{ $t('packing.templates.empty') }}
      </p>
    </div>
    <div class="flex flex-col gap-2">
      <InputText
        v-model="newName"
        :placeholder="$t('packing.templates.newPlaceholder')"
        size="small"
        @keyup.enter="create"
      />
      <div class="flex gap-2">
        <!-- dueño de la plantilla nueva (solo aparece si hay más dueños posibles) -->
        <Select
          v-if="ownerOptions.length > 1"
          v-model="newOwner"
          :options="ownerOptions"
          optionLabel="label"
          optionValue="value"
          :aria-label="$t('packing.templates.owner')"
          class="flex-1"
          size="small"
        >
          <template #option="{ option }">
            <span class="flex items-center gap-2 min-w-0">
              <span class="w-4 h-4 grid place-items-center overflow-hidden shrink-0">
                <TravelerAvatar
                  :name="option.name"
                  :color="option.color"
                  :avatar-url="option.avatarUrl"
                  size="xs"
                />
              </span>
              <span class="truncate">{{ option.label }}</span>
            </span>
          </template>
          <template #value="{ placeholder }">
            <span v-if="selectedOwner" class="flex items-center gap-2 min-w-0">
              <span class="w-4 h-4 grid place-items-center overflow-hidden shrink-0">
                <TravelerAvatar
                  :name="selectedOwner.name"
                  :color="selectedOwner.color"
                  :avatar-url="selectedOwner.avatarUrl"
                  size="xs"
                />
              </span>
              <span class="truncate">{{ selectedOwner.label }}</span>
            </span>
            <span v-else>{{ placeholder }}</span>
          </template>
        </Select>
        <span v-else class="flex-1" />
        <Button icon="pi pi-plus" size="small" @click="create" />
      </div>
    </div>
  </div>
</template>
