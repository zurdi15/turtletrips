<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import TravelerItem from './TravelerItem.vue'
import type { Family, Traveler } from '../../api/types'
import { useConfirmDelete } from '../../composables/useConfirmDelete'
import { useNotify } from '../../composables/useNotify'
import { useFamiliesStore } from '../../stores/families'
import { useSessionStore } from '../../stores/session'
import { useUsersStore } from '../../stores/users'

// family=null agrupa a los viajeros sin familia (solo se pinta si hay alguno)
const props = defineProps<{ family: Family | null; travelers: Traveler[] }>()
defineEmits<{
  rename: [traveler: Traveler, name: string]
  remove: [traveler: Traveler]
  'pick-color': [event: Event, traveler: Traveler]
  'open-menu': [event: Event, traveler: Traveler]
}>()

const { t } = useI18n()
const notify = useNotify()
const confirmAction = useConfirmDelete()
const families = useFamiliesStore()
const session = useSessionStore()

const editing = ref(false)
const editName = ref('')

function startEdit() {
  if (!props.family) return
  editing.value = true
  editName.value = props.family.name
}

async function confirmEdit() {
  if (!props.family) return
  const name = editName.value.trim()
  if (!name) return
  try {
    await families.update(props.family.id, { name })
    editing.value = false
  } catch (err) {
    notify.error(t('travelers.families.toast.renameError'), err)
  }
}

function removeFamily() {
  const family = props.family
  if (!family) return
  confirmAction({
    message: t('travelers.families.confirmDelete.message', { name: family.name }),
    header: t('travelers.families.confirmDelete.header'),
    accept: async () => {
      try {
        await families.remove(family.id)
      } catch (err) {
        notify.error(t('travelers.families.toast.deleteError'), err)
      }
    },
  })
}

function canEdit(traveler: Traveler): boolean {
  return session.isAdmin || !traveler.has_user || traveler.id === session.travelerId
}

// nombre de cuenta: del listado de usuarios (solo lo carga el admin) o el
// propio de la sesión; para el resto queda oculto a propósito
const users = useUsersStore()
function usernameOf(traveler: Traveler): string | null {
  if (traveler.id === session.travelerId) return session.me?.user.username ?? null
  return users.items.find((user) => user.traveler.id === traveler.id)?.username ?? null
}
</script>

<template>
  <section class="bg-surface rounded-card border border-line p-4">
    <div class="flex items-center gap-2 mb-2 px-3 group">
      <!-- asa del drag & drop de familias (el <draggable> vive en la vista) -->
      <i
        v-if="family && session.isAdmin"
        class="pi pi-bars text-xs text-ink-faint hover:text-ink-secondary tt-drag-handle cursor-grab active:cursor-grabbing"
        v-tooltip.top="t('travelers.families.dragHint')"
      />
      <i
        class="text-sm pi pi-users"
      />
      <template v-if="editing">
        <InputText
          v-model="editName"
          class="flex-1"
          size="small"
          autofocus
          @keyup.enter="confirmEdit"
          @keyup.escape="editing = false"
        />
        <Button icon="pi pi-check" text size="small" @click="confirmEdit" />
        <Button icon="pi pi-times" text size="small" severity="secondary" @click="editing = false" />
      </template>
      <template v-else>
        <h2 class="flex-1 font-semibold text-ink truncate">
          {{ family?.name ?? t('travelers.families.none') }}
        </h2>
        <span class="text-2xs text-ink-faint">{{ travelers.length }}</span>
        <div v-if="family && session.isAdmin" class="flex gap-1">
          <Button icon="pi pi-pencil" text size="small" severity="secondary" @click="startEdit" />
          <Button icon="pi pi-trash" text size="small" severity="danger" @click="removeFamily" />
        </div>
      </template>
    </div>
    <!-- entrada/salida/recolocación suave al crear, borrar o mover viajeros -->
    <TransitionGroup tag="ul" name="tt-list" class="relative flex flex-col gap-1">
      <TravelerItem
        v-for="traveler in travelers"
        :key="traveler.id"
        :traveler="traveler"
        :is-self="traveler.id === session.travelerId"
        :username="usernameOf(traveler)"
        :can-edit="canEdit(traveler)"
        :can-remove="canEdit(traveler) && !traveler.has_user"
        :show-admin-menu="session.isAdmin"
        @rename="(name) => $emit('rename', traveler, name)"
        @remove="$emit('remove', traveler)"
        @pick-color="(event) => $emit('pick-color', event, traveler)"
        @open-menu="(event) => $emit('open-menu', event, traveler)"
      />
    </TransitionGroup>
    <p v-if="!travelers.length" class="text-sm text-ink-faint px-3 py-2">
      {{ t('travelers.families.empty') }}
    </p>
  </section>
</template>
