<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Pill from '../ui/Pill.vue'
import TravelerAvatar from '../ui/TravelerAvatar.vue'
import UserFormDialog from './UserFormDialog.vue'
import ResetPasswordDialog from './ResetPasswordDialog.vue'
import type { User } from '../../api/types'
import { useConfirmDelete } from '../../composables/useConfirmDelete'
import { useNotify } from '../../composables/useNotify'
import { useFamiliesStore } from '../../stores/families'
import { useSessionStore } from '../../stores/session'
import { useUsersStore } from '../../stores/users'

const { t } = useI18n()
const notify = useNotify()
const confirmAction = useConfirmDelete()
const users = useUsersStore()
const families = useFamiliesStore()
const session = useSessionStore()

const showForm = ref(false)
const showReset = ref(false)
const resetTarget = ref<User | null>(null)

function familyName(user: User): string | null {
  const id = user.traveler.family_id
  return id === null ? null : (families.items.find((f) => f.id === id)?.name ?? null)
}

function isSelf(user: User): boolean {
  return user.id === session.me?.user.id
}

function openReset(user: User) {
  resetTarget.value = user
  showReset.value = true
}

async function toggleAdmin(user: User) {
  try {
    await users.update(user.id, { is_admin: !user.is_admin })
  } catch (err) {
    notify.error(t('admin.users.toast.updateError'), err)
  }
}

function removeUser(user: User) {
  confirmAction({
    message: t('admin.users.confirmDelete.message', { name: user.username }),
    header: t('admin.users.confirmDelete.header'),
    accept: async () => {
      try {
        await users.remove(user.id)
      } catch (err) {
        notify.error(t('admin.users.toast.deleteError'), err)
      }
    },
  })
}
</script>

<template>
  <section class="bg-surface rounded-card border border-line p-5">
    <div class="flex items-start justify-between gap-3 mb-1">
      <h2 class="font-semibold text-ink">{{ t('admin.users.title') }}</h2>
      <Button
        :label="t('admin.users.new')"
        icon="pi pi-plus"
        size="small"
        @click="showForm = true"
      />
    </div>
    <p class="text-xs text-ink-faint mb-4">{{ t('admin.users.hint') }}</p>

    <ul class="flex flex-col gap-1.5">
      <li
        v-for="user in users.items"
        :key="user.id"
        class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-surface-hover group"
      >
        <TravelerAvatar
          :name="user.traveler.name"
          :color="user.traveler.color"
          :avatar-url="user.traveler.avatar_url"
          size="md"
        />
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 flex-wrap">
            <span class="font-medium text-ink">{{ user.username }}</span>
            <Pill v-if="user.is_admin" color="brand" icon="pi pi-shield">
              {{ t('admin.users.isAdmin') }}
            </Pill>
            <Pill v-if="isSelf(user)" color="info">{{ t('admin.users.you') }}</Pill>
          </div>
          <div class="text-2xs text-ink-muted truncate">
            {{ user.traveler.name
            }}<template v-if="familyName(user)"> · {{ familyName(user) }}</template>
          </div>
        </div>
        <div class="flex gap-1 hover-actions">
          <Button
            icon="pi pi-key"
            text
            size="small"
            severity="secondary"
            v-tooltip.top="t('admin.users.resetPassword')"
            @click="openReset(user)"
          />
          <Button
            icon="pi pi-shield"
            text
            size="small"
            :severity="user.is_admin ? 'primary' : 'secondary'"
            :disabled="isSelf(user)"
            v-tooltip.top="t('admin.users.isAdmin')"
            @click="toggleAdmin(user)"
          />
          <Button
            icon="pi pi-trash"
            text
            size="small"
            severity="danger"
            :disabled="isSelf(user)"
            @click="removeUser(user)"
          />
        </div>
      </li>
    </ul>

    <UserFormDialog v-model:visible="showForm" />
    <ResetPasswordDialog v-model:visible="showReset" :user="resetTarget" />
  </section>
</template>
