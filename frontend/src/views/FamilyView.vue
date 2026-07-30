<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import ToggleSwitch from 'primevue/toggleswitch'
import PageHeader from '../components/ui/PageHeader.vue'
import ColorSwatchPopover from '../components/ui/ColorSwatchPopover.vue'
import EmptyState from '../components/EmptyState.vue'
import TravelerItem from '../components/travelers/TravelerItem.vue'
import type { Traveler } from '../api/types'
import { useBagPermissionsStore } from '../stores/bagPermissions'
import { useSessionStore } from '../stores/session'
import { useTravelersStore } from '../stores/travelers'
import { useConfirmDelete } from '../composables/useConfirmDelete'
import { useNotify } from '../composables/useNotify'

// Tu familia: quiénes son y qué les dejas hacer con TUS maletas (default:
// permitido, aquí se revoca). La gestión de cuentas y familias vive en el
// panel de administración (/admin), no aquí.

const travelers = useTravelersStore()
const session = useSessionStore()
const bagPerms = useBagPermissionsStore()
const confirmAction = useConfirmDelete()
const notify = useNotify()
const { t } = useI18n()

const myFamilyId = computed(() => session.me?.traveler.family_id ?? null)
const familyName = computed(() => session.me?.family?.name ?? t('family.title'))

onMounted(() => {
  travelers.load(true)
  if (myFamilyId.value != null) bagPerms.load(true)
})

// yo primero, luego el resto de cuentas y al final los virtuales
const members = computed(() => {
  const mine = travelers.items.filter((trav) => trav.family_id === myFamilyId.value)
  const self = mine.filter((trav) => trav.id === session.travelerId)
  const accounts = mine.filter((trav) => trav.id !== session.travelerId && trav.has_user)
  const virtuals = mine.filter((trav) => trav.id !== session.travelerId && !trav.has_user)
  const byName = (a: Traveler, b: Traveler) => a.name.localeCompare(b.name)
  return [...self, ...accounts.sort(byName), ...virtuals.sort(byName)]
})

function canEdit(traveler: Traveler): boolean {
  return session.isAdmin || !traveler.has_user || traveler.id === session.travelerId
}

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

// --- permiso de maletas: default permitido, el toggle revoca/devuelve ---

function bagAllowed(traveler: Traveler): boolean {
  return !bagPerms.revoked.has(traveler.id)
}

async function setBagAllowed(traveler: Traveler, allowed: boolean) {
  try {
    await bagPerms.setAllowed(traveler.id, allowed)
  } catch (err) {
    notify.error(t('family.toast.permissionError'), err)
  }
}
</script>

<template>
  <div class="max-w-2xl mx-auto">
    <PageHeader :title="t('family.title')" :info="t('family.info')" class="mb-6" />

    <EmptyState
      v-if="myFamilyId == null"
      icon="pi pi-users"
      :title="t('family.empty.title')"
      :subtitle="t('family.empty.subtitle')"
    />

    <section v-else class="tt-anim-rise bg-surface rounded-card border border-line p-4">
      <div class="flex items-center gap-2 mb-2 px-3">
        <i class="text-sm pi pi-users" />
        <h2 class="flex-1 font-semibold text-ink truncate">{{ familyName }}</h2>
        <span class="text-2xs text-ink-faint">{{ members.length }}</span>
      </div>
      <TransitionGroup tag="ul" name="tt-list" class="relative flex flex-col gap-1">
        <TravelerItem
          v-for="member in members"
          :key="member.id"
          :traveler="member"
          :is-self="member.id === session.travelerId"
          :username="member.id === session.travelerId ? (session.me?.user.username ?? null) : null"
          :can-edit="canEdit(member)"
          :can-remove="canEdit(member) && !member.has_user"
          :show-admin-menu="false"
          @rename="(name) => rename(member, name)"
          @remove="remove(member)"
          @pick-color="(event) => openColorPicker(event, member)"
        >
          <!-- si este miembro puede gestionar TUS maletas (default: sí) -->
          <ToggleSwitch
            v-if="member.has_user && member.id !== session.travelerId"
            :modelValue="bagAllowed(member)"
            class="shrink-0 scale-75"
            v-tooltip.top="t('family.bagPermissionTooltip', { name: member.name })"
            @update:modelValue="(value: boolean) => setBagAllowed(member, value)"
          />
        </TravelerItem>
      </TransitionGroup>
      <p v-if="members.length > 1" class="text-xs text-ink-faint px-3 pt-3">
        <i class="pi pi-briefcase text-3xs" /> {{ t('family.bagPermissionHint') }}
      </p>
    </section>

    <ColorSwatchPopover ref="colorPopover" @select="pickColor" />
  </div>
</template>
