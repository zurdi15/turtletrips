<script setup lang="ts">
import { onMounted, ref } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import PageHeader from '../components/ui/PageHeader.vue'
import EditableListItem from '../components/ui/EditableListItem.vue'
import ColorSwatchPopover from '../components/ui/ColorSwatchPopover.vue'
import Pill from '../components/ui/Pill.vue'
import type { Traveler } from '../api/types'
import { CATEGORY_PALETTE } from '../theme'
import { FALLBACK_CATEGORY_COLOR } from '../stores/categories'
import { useFamiliesStore } from '../stores/families'
import { useTravelersStore } from '../stores/travelers'
import { useConfirmDelete } from '../composables/useConfirmDelete'
import { useNotify } from '../composables/useNotify'
import { useI18n } from 'vue-i18n'

const travelers = useTravelersStore()
const families = useFamiliesStore()
const confirmAction = useConfirmDelete()
const notify = useNotify()
const { t } = useI18n()

const newName = ref('')
const colorTargetId = ref<number | null>(null)
const colorPopover = ref<InstanceType<typeof ColorSwatchPopover>>()

onMounted(() => {
  travelers.load(true)
  families.load()
})

function familyName(traveler: Traveler): string | null {
  if (traveler.family_id === null) return null
  return families.items.find((f) => f.id === traveler.family_id)?.name ?? null
}

function openColorPicker(event: Event, id: number) {
  colorTargetId.value = id
  colorPopover.value?.toggle(event)
}

async function pickColor(color: string) {
  if (colorTargetId.value == null) return
  await travelers.update(colorTargetId.value, { color })
}

async function add() {
  const name = newName.value.trim()
  if (!name) return
  try {
    await travelers.create(name, CATEGORY_PALETTE[travelers.items.length % CATEGORY_PALETTE.length])
    newName.value = ''
  } catch (err) {
    notify.error(t('travelers.toast.addError'), err)
  }
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
    accept: () => travelers.remove(traveler.id),
  })
}
</script>

<template>
  <div class="max-w-2xl mx-auto">
    <PageHeader
      :title="t('travelers.title')"
      :info="t('travelers.info')"
      class="mb-6"
    />

    <div class="bg-surface rounded-card border border-line p-5">
      <ul class="tt-stagger flex flex-col gap-1.5 mb-4">
        <EditableListItem
          v-for="traveler in travelers.items"
          :key="traveler.id"
          :name="traveler.name"
          :color="traveler.color"
          :colorFallback="FALLBACK_CATEGORY_COLOR"
          :avatar-url="traveler.avatar_url"
          @rename="(name) => rename(traveler, name)"
          @remove="remove(traveler)"
          @pick-color="(event) => openColorPicker(event, traveler.id)"
        >
          <Pill
            v-if="traveler.has_user"
            color="brand"
            icon="pi pi-user"
            v-tooltip.top="t('travelers.badges.accountTooltip')"
          >
            {{ t('travelers.badges.account') }}
          </Pill>
          <Pill v-if="familyName(traveler)" color="neutral" icon="pi pi-home">
            {{ familyName(traveler) }}
          </Pill>
        </EditableListItem>
        <li v-if="!travelers.items.length" class="text-sm text-ink-faint px-3 py-4 text-center">
          {{ t('travelers.empty') }}
        </li>
      </ul>
      <div class="flex gap-2">
        <InputText
          v-model="newName"
          :placeholder="t('travelers.newPlaceholder')"
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
    </div>

    <ColorSwatchPopover ref="colorPopover" @select="pickColor" />
  </div>
</template>
