<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import MultiSelect from 'primevue/multiselect'
import RowActions from '../ui/RowActions.vue'
import type { Family } from '../../api/types'
import { useConfirmDelete } from '../../composables/useConfirmDelete'
import { useNotify } from '../../composables/useNotify'
import { useFamiliesStore } from '../../stores/families'
import { useTravelersStore } from '../../stores/travelers'

const { t } = useI18n()
const notify = useNotify()
const confirmAction = useConfirmDelete()
const families = useFamiliesStore()
const travelers = useTravelersStore()

const newName = ref('')
const editingId = ref<number | null>(null)
const editName = ref('')

// viajeros por familia, derivado de la lista global (family_id vive en el viajero)
const membersByFamily = computed(() => {
  const map = new Map<number, number[]>()
  for (const traveler of travelers.items) {
    if (traveler.family_id === null) continue
    map.set(traveler.family_id, [...(map.get(traveler.family_id) ?? []), traveler.id])
  }
  return map
})

async function add() {
  const name = newName.value.trim()
  if (!name) return
  try {
    await families.create({ name })
    newName.value = ''
  } catch (err) {
    notify.error(t('admin.families.toast.addError'), err)
  }
}

function startEdit(family: Family) {
  editingId.value = family.id
  editName.value = family.name
}

async function confirmEdit(family: Family) {
  const name = editName.value.trim()
  if (!name) return
  try {
    await families.update(family.id, { name })
    editingId.value = null
  } catch (err) {
    notify.error(t('admin.families.toast.renameError'), err)
  }
}

function removeFamily(family: Family) {
  confirmAction({
    message: t('admin.families.confirmDelete.message', { name: family.name }),
    header: t('admin.families.confirmDelete.header'),
    accept: async () => {
      try {
        await families.remove(family.id)
      } catch (err) {
        notify.error(t('admin.families.toast.deleteError'), err)
      }
    },
  })
}

async function setMembers(family: Family, ids: number[]) {
  const current = membersByFamily.value.get(family.id) ?? []
  const added = ids.filter((id) => !current.includes(id))
  const removed = current.filter((id) => !ids.includes(id))
  try {
    for (const id of added) await travelers.update(id, { family_id: family.id })
    for (const id of removed) await travelers.update(id, { family_id: null })
  } catch (err) {
    notify.error(t('admin.families.toast.assignError'), err)
    travelers.load(true)
  }
}
</script>

<template>
  <section class="bg-surface rounded-card border border-line p-5">
    <h2 class="font-semibold text-ink mb-1">{{ t('admin.families.title') }}</h2>
    <p class="text-xs text-ink-faint mb-4">{{ t('admin.families.hint') }}</p>

    <ul class="flex flex-col gap-3 mb-4">
      <li
        v-for="family in families.items"
        :key="family.id"
        class="px-3 py-2 rounded-lg border border-line-subtle group"
      >
        <div class="flex items-center gap-2 mb-2">
          <template v-if="editingId === family.id">
            <InputText
              v-model="editName"
              class="flex-1"
              size="small"
              autofocus
              @keyup.enter="confirmEdit(family)"
              @keyup.escape="editingId = null"
            />
            <Button icon="pi pi-check" text size="small" @click="confirmEdit(family)" />
            <Button icon="pi pi-times" text size="small" severity="secondary" @click="editingId = null" />
          </template>
          <template v-else>
            <span class="flex-1 font-medium text-ink">{{ family.name }}</span>
            <RowActions @edit="startEdit(family)" @remove="removeFamily(family)" />
          </template>
        </div>
        <MultiSelect
          :model-value="membersByFamily.get(family.id) ?? []"
          :options="travelers.items"
          option-label="name"
          option-value="id"
          display="chip"
          filter
          class="w-full"
          :placeholder="t('admin.families.empty')"
          :aria-label="t('admin.families.members')"
          @update:model-value="(ids: number[]) => setMembers(family, ids)"
        />
      </li>
    </ul>

    <div class="flex gap-2">
      <InputText
        v-model="newName"
        :placeholder="t('admin.families.newPlaceholder')"
        class="flex-1 min-w-0"
        @keyup.enter="add"
      />
      <Button
        :label="t('common.actions.add')"
        icon="pi pi-plus"
        class="shrink-0 max-sm:[&_.p-button-label]:hidden"
        @click="add"
      />
    </div>
  </section>
</template>
