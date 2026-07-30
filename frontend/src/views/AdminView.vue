<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import draggable from 'vuedraggable'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Popover from 'primevue/popover'
import PageHeader from '../components/ui/PageHeader.vue'
import ColorSwatchPopover from '../components/ui/ColorSwatchPopover.vue'
import FamilyGroup from '../components/travelers/FamilyGroup.vue'
import TravelerFormDialog from '../components/travelers/TravelerFormDialog.vue'
import AccountCreateDialog from '../components/travelers/AccountCreateDialog.vue'
import ResetPasswordDialog from '../components/travelers/ResetPasswordDialog.vue'
import type { Traveler } from '../api/types'
import { useFamiliesStore } from '../stores/families'
import { useSessionStore } from '../stores/session'
import { useTravelersStore } from '../stores/travelers'
import { useUsersStore } from '../stores/users'
import { useConfirmDelete } from '../composables/useConfirmDelete'
import { useNotify } from '../composables/useNotify'

const travelers = useTravelersStore()
const families = useFamiliesStore()
const users = useUsersStore()
const session = useSessionStore()
const confirmAction = useConfirmDelete()
const notify = useNotify()
const { t } = useI18n()

onMounted(() => {
  travelers.load(true)
  families.load(true)
  if (session.isAdmin) users.load(true)
})

// viajeros por familia (null = huérfanos, se pintan en su propio grupo al final)
const travelersByFamily = computed(() => {
  const map = new Map<number | null, Traveler[]>()
  for (const traveler of travelers.items) {
    const key = traveler.family_id
    map.set(key, [...(map.get(key) ?? []), traveler])
  }
  return map
})
const orphans = computed(() => travelersByFamily.value.get(null) ?? [])

// mapa traveler → user para las acciones de cuenta (solo lo carga el admin)
const userByTraveler = computed(
  () => new Map(users.items.map((user) => [user.traveler.id, user])),
)

// ---- alta y CRUD de viajeros ----

const showTravelerForm = ref(false)

async function rename(traveler: Traveler, name: string) {
  try {
    await travelers.update(traveler.id, { name })
  } catch (err) {
    notify.error(t('travelers.toast.renameError'), err)
  }
}

function remove(traveler: Traveler) {
  confirmAction({
    message: t('travelers.confirmDelete.message', { name: traveler.name }),
    header: t('travelers.confirmDelete.header'),
    accept: async () => {
      try {
        await travelers.remove(traveler.id)
      } catch (err) {
        notify.error(t('travelers.toast.deleteError'), err)
      }
    },
  })
}

// ---- color ----

const colorTargetId = ref<number | null>(null)
const colorPopover = ref<InstanceType<typeof ColorSwatchPopover>>()

function openColorPicker(event: Event, traveler: Traveler) {
  colorTargetId.value = traveler.id
  colorPopover.value?.toggle(event)
}

async function pickColor(color: string) {
  if (colorTargetId.value == null) return
  const updated = await travelers.update(colorTargetId.value, { color })
  session.setTraveler(updated)
}

// ---- familias: alta rápida y orden con drag & drop (admin) ----

const newFamilyName = ref('')

async function addFamily() {
  const name = newFamilyName.value.trim()
  if (!name) return
  try {
    await families.create({ name })
    newFamilyName.value = ''
  } catch (err) {
    notify.error(t('travelers.families.toast.addError'), err)
  }
}

async function persistFamilyOrder() {
  // draggable ya reordenó families.items en sitio; solo hay que persistirlo
  try {
    await families.reorder(families.items.map((family) => family.id))
  } catch (err) {
    notify.error(t('travelers.families.toast.reorderError'), err)
    families.load(true)
  }
}

// ---- menú admin por viajero (cuenta + familia) ----

const menuPopover = ref<InstanceType<typeof Popover> | null>(null)
const menuTarget = ref<Traveler | null>(null)
const menuUser = computed(() =>
  menuTarget.value ? (userByTraveler.value.get(menuTarget.value.id) ?? null) : null,
)
const menuIsSelf = computed(() => menuTarget.value?.id === session.travelerId)

function openMenu(event: Event, traveler: Traveler) {
  menuTarget.value = traveler
  menuPopover.value?.toggle(event)
}

const showAccountForm = ref(false)
const showReset = ref(false)

function createAccount() {
  menuPopover.value?.hide()
  showAccountForm.value = true
}

function resetPassword() {
  menuPopover.value?.hide()
  showReset.value = true
}

async function toggleAdmin() {
  const user = menuUser.value
  if (!user) return
  menuPopover.value?.hide()
  try {
    await users.update(user.id, { is_admin: !user.is_admin })
  } catch (err) {
    notify.error(t('travelers.account.toast.updateError'), err)
  }
}

function removeAccount() {
  const user = menuUser.value
  if (!user) return
  menuPopover.value?.hide()
  confirmAction({
    message: t('travelers.account.confirmDelete.message', { name: user.username }),
    header: t('travelers.account.confirmDelete.header'),
    accept: async () => {
      try {
        await users.remove(user.id)
        travelers.load(true)
      } catch (err) {
        notify.error(t('travelers.account.toast.deleteError'), err)
      }
    },
  })
}

async function moveFamily(familyId: number | null) {
  const traveler = menuTarget.value
  menuPopover.value?.hide()
  if (!traveler || traveler.family_id === familyId) return
  try {
    await travelers.update(traveler.id, { family_id: familyId })
  } catch (err) {
    notify.error(t('travelers.families.toast.assignError'), err)
  }
}
</script>

<template>
  <div class="max-w-2xl mx-auto">
    <PageHeader :title="t('travelers.adminTitle')" :info="t('travelers.adminInfo')" class="mb-6" />

    <div class="flex flex-col gap-4">
      <!-- tarjetas de familia: cascada al montar y drag & drop para ordenarlas (admin) -->
      <draggable
        :list="families.items"
        item-key="id"
        handle=".tt-drag-handle"
        :disabled="!session.isAdmin"
        ghost-class="opacity-40"
        tag="div"
        class="tt-stagger flex flex-col gap-4 empty:hidden"
        @end="persistFamilyOrder"
      >
        <template #item="{ element }">
          <FamilyGroup
            :family="element"
            :travelers="travelersByFamily.get(element.id) ?? []"
            @rename="rename"
            @remove="remove"
            @pick-color="openColorPicker"
            @open-menu="openMenu"
          />
        </template>
      </draggable>

      <FamilyGroup
        v-if="orphans.length"
        class="tt-anim-rise"
        :family="null"
        :travelers="orphans"
        @rename="rename"
        @remove="remove"
        @pick-color="openColorPicker"
        @open-menu="openMenu"
      />

      <p v-if="!travelers.items.length" class="text-sm text-ink-faint px-3 py-2 text-center">
        {{ t('travelers.empty') }}
      </p>

      <div class="tt-anim-rise bg-surface rounded-card border border-line p-4 flex flex-col gap-2">
        <Button
          :label="t('travelers.newAction')"
          icon="pi pi-user-plus"
          class="self-start"
          @click="showTravelerForm = true"
        />
        <div v-if="session.isAdmin" class="flex gap-2">
          <InputText
            v-model="newFamilyName"
            :placeholder="t('travelers.families.newPlaceholder')"
            class="flex-1 min-w-0"
            @keyup.enter="addFamily"
          />
          <Button
            :label="t('common.actions.add')"
            icon="pi pi-plus"
            severity="secondary"
            outlined
            class="shrink-0 max-sm:[&_.p-button-label]:hidden"
            @click="addFamily"
          />
        </div>
      </div>
    </div>

    <ColorSwatchPopover ref="colorPopover" @select="pickColor" />

    <!-- menú admin compartido: cuenta del viajero + familia -->
    <Popover ref="menuPopover">
      <div v-if="menuTarget" class="tt-stagger flex flex-col min-w-52">
        <button
          v-if="!menuTarget.has_user"
          type="button"
          class="flex items-center gap-2 px-3 py-2 text-sm text-left rounded-lg text-ink-secondary hover:bg-surface-hover hover:text-ink transition-colors"
          @click="createAccount"
        >
          <i class="pi pi-user-plus text-sm" /> {{ t('travelers.account.createAction') }}
        </button>
        <template v-else-if="menuUser">
          <button
            type="button"
            class="flex items-center gap-2 px-3 py-2 text-sm text-left rounded-lg text-ink-secondary hover:bg-surface-hover hover:text-ink transition-colors"
            @click="resetPassword"
          >
            <i class="pi pi-key text-sm" /> {{ t('travelers.account.resetPassword') }}
          </button>
          <!-- deshabilitado = claramente mute: tinta apagada, sin hover y cursor de no-permitido -->
          <button
            type="button"
            class="flex items-center gap-2 px-3 py-2 text-sm text-left rounded-lg transition-colors text-ink-secondary enabled:hover:bg-surface-hover enabled:hover:text-ink disabled:text-ink-disabled disabled:cursor-not-allowed"
            :disabled="menuIsSelf"
            @click="toggleAdmin"
          >
            <i class="pi pi-shield text-sm" />
            {{ menuUser.is_admin ? t('travelers.account.revokeAdmin') : t('travelers.account.makeAdmin') }}
          </button>
          <button
            type="button"
            class="flex items-center gap-2 px-3 py-2 text-sm text-left rounded-lg transition-colors text-red-600 enabled:hover:bg-surface-hover disabled:text-ink-disabled disabled:cursor-not-allowed"
            :disabled="menuIsSelf"
            @click="removeAccount"
          >
            <i class="pi pi-user-minus text-sm" /> {{ t('travelers.account.deleteAction') }}
          </button>
        </template>
        <div class="border-t border-line-subtle mt-1 pt-1">
          <div class="px-3 py-1 text-2xs uppercase tracking-wide text-ink-faint">
            {{ t('travelers.families.moveTitle') }}
          </div>
          <button
            v-for="family in families.items"
            :key="family.id"
            type="button"
            class="w-full flex items-center gap-2 px-3 py-1.5 text-sm text-left rounded-lg text-ink-secondary hover:bg-surface-hover hover:text-ink transition-colors"
            @click="moveFamily(family.id)"
          >
            <i
              class="pi pi-check text-xs"
              :class="menuTarget.family_id === family.id ? '' : 'invisible'"
            />
            {{ family.name }}
          </button>
          <button
            type="button"
            class="w-full flex items-center gap-2 px-3 py-1.5 text-sm text-left rounded-lg text-ink-secondary hover:bg-surface-hover hover:text-ink transition-colors"
            @click="moveFamily(null)"
          >
            <i
              class="pi pi-check text-xs"
              :class="menuTarget.family_id === null ? '' : 'invisible'"
            />
            {{ t('travelers.families.none') }}
          </button>
        </div>
      </div>
    </Popover>

    <TravelerFormDialog v-model:visible="showTravelerForm" />
    <AccountCreateDialog v-model:visible="showAccountForm" :traveler="menuTarget" />
    <ResetPasswordDialog v-model:visible="showReset" :user="menuUser" />
  </div>
</template>
