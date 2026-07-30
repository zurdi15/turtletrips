<script setup lang="ts">
import { ref } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Pill from '../ui/Pill.vue'
import type { Traveler } from '../../api/types'
import { FALLBACK_CATEGORY_COLOR } from '../../stores/categories'

const props = defineProps<{
  traveler: Traveler
  /** es el viajero de la sesión actual */
  isSelf: boolean
  /** puede renombrar / cambiar color-foto (propio, virtual o admin) */
  canEdit: boolean
  /** puede borrarse (solo virtuales, con permisos) */
  canRemove: boolean
  /** menú de administración (cuenta y familia), solo admin */
  showAdminMenu: boolean
  /** nombre de la cuenta: solo lo ven el admin (panel) y uno mismo */
  username?: string | null
}>()
const emit = defineEmits<{
  rename: [name: string]
  remove: []
  /** clic en el dot/foto: el padre abre su ColorSwatchPopover */
  'pick-color': [event: Event]
  /** clic en el menú admin: el padre abre su Popover compartido */
  'open-menu': [event: Event]
}>()

const editing = ref(false)
const editName = ref('')

function startEdit() {
  editing.value = true
  editName.value = props.traveler.name
}

function confirmEdit() {
  const name = editName.value.trim()
  if (!name) return
  emit('rename', name)
  editing.value = false
}
</script>

<template>
  <li class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-surface-hover group">
    <button
      class="w-6 h-6 rounded-full shrink-0 ring-1 ring-line transition-transform overflow-hidden"
      :class="canEdit ? 'hover:scale-110' : 'cursor-default'"
      :style="
        traveler.avatar_url
          ? undefined
          : { background: traveler.color ?? FALLBACK_CATEGORY_COLOR }
      "
      v-tooltip.top="canEdit ? $t('common.actions.changeColor') : undefined"
      :disabled="!canEdit"
      @click="$emit('pick-color', $event)"
    >
      <img
        v-if="traveler.avatar_url"
        :src="traveler.avatar_url"
        :alt="traveler.name"
        class="w-full h-full object-cover"
      />
    </button>
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
      <span class="flex-1 min-w-0 flex items-baseline gap-2">
        <span class="text-ink font-medium truncate">{{ traveler.name }}</span>
        <span v-if="username" class="text-xs text-ink-faint font-mono truncate">
          @{{ username }}
        </span>
      </span>
      <Pill v-if="isSelf" color="info" pop-in>{{ $t('travelers.badges.you') }}</Pill>
      <Pill
        v-else-if="traveler.has_user"
        color="brand"
        icon="pi pi-user"
        pop-in
        v-tooltip.top="$t('travelers.badges.accountTooltip')"
      >
        {{ $t('travelers.badges.account') }}
      </Pill>
      <!-- extras del contexto (p. ej. el toggle de permiso de maletas en Familia) -->
      <slot />
      <div class="flex gap-1">
        <Button
          v-if="canEdit"
          icon="pi pi-pencil"
          text
          size="small"
          severity="secondary"
          @click="startEdit"
        />
        <Button
          v-if="canRemove"
          icon="pi pi-trash"
          text
          size="small"
          severity="danger"
          @click="$emit('remove')"
        />
        <Button
          v-if="showAdminMenu"
          icon="pi pi-ellipsis-v"
          text
          size="small"
          severity="secondary"
          @click="$emit('open-menu', $event)"
        />
      </div>
    </template>
  </li>
</template>
