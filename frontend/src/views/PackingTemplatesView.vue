<script setup lang="ts">
import { computed, onMounted, ref, watchEffect } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import EmptyState from '../components/EmptyState.vue'
import PageHeader from '../components/ui/PageHeader.vue'
import TravelerAvatar from '../components/ui/TravelerAvatar.vue'
import PackingAddBar from '../components/packing/PackingAddBar.vue'
import PackingCategoryCard from '../components/packing/PackingCategoryCard.vue'
import TemplateList, { type TemplateOwnerGroup } from '../components/packing/TemplateList.vue'
import TemplateItemRow from '../components/packing/TemplateItemRow.vue'
import type { PackingTemplateItem, Traveler } from '../api/types'
import { usePackingTemplatesStore } from '../stores/packingTemplates'
import { useCategoriesStore } from '../stores/categories'
import { useTravelersStore } from '../stores/travelers'
import { useSessionStore } from '../stores/session'
import { useConfirmDelete } from '../composables/useConfirmDelete'
import { useNotify } from '../composables/useNotify'
import { groupPackingItems } from '../utils/packing'

const store = usePackingTemplatesStore()
const categories = useCategoriesStore()
const travelers = useTravelersStore()
const session = useSessionStore()
const confirmAction = useConfirmDelete()
const notify = useNotify()
const { t } = useI18n()

const renaming = ref(false)
const renameValue = ref('')

onMounted(() => {
  store.load()
  categories.load('packing')
  travelers.load()
})

const categoryOptions = computed(() =>
  categories.packing.map((c) => ({ value: c.name, label: c.name })),
)

// --- matriz familiar: toda tu familia se VE; editas lo tuyo y lo de virtuales ---

const myFamilyId = computed(() => session.me?.traveler.family_id ?? null)

// virtuales cuya plantilla puede poseer un no-admin: los de su familia
const ownableVirtuals = computed(() =>
  travelers.items.filter(
    (trav) => !trav.has_user && trav.family_id != null && trav.family_id === myFamilyId.value,
  ),
)

// dueños posibles al CREAR: tú + tus virtuales; el admin, CUALQUIER viajero
const ownerOptions = computed(() => {
  if (session.travelerId == null || !session.me) return []
  const me = session.me.traveler
  const rest = session.isAdmin
    ? travelers.items.filter((trav) => trav.id !== me.id)
    : ownableVirtuals.value
  const toOption = (trav: Traveler, label?: string) => ({
    value: trav.id,
    label: label ?? trav.name,
    name: trav.name,
    color: trav.color,
    avatarUrl: trav.avatar_url,
  })
  return [toOption(me, t('packing.templates.ownerYou')), ...rest.map((trav) => toOption(trav))]
})

function travelerById(id: number): Traveler | null {
  if (id === session.travelerId && session.me) return session.me.traveler
  return travelers.items.find((trav) => trav.id === id) ?? null
}

// plantillas agrupadas por dueño: las tuyas primero, luego el resto de la familia
const groups = computed<TemplateOwnerGroup[]>(() => {
  const byOwner = new Map<number, TemplateOwnerGroup>()
  for (const template of store.templates) {
    let group = byOwner.get(template.traveler_id)
    if (!group) {
      const owner = travelerById(template.traveler_id)
      group = {
        ownerId: template.traveler_id,
        name: owner?.name ?? '—',
        color: owner?.color ?? null,
        avatarUrl: owner?.avatar_url ?? null,
        isYou: template.traveler_id === session.travelerId,
        templates: [],
      }
      byOwner.set(template.traveler_id, group)
    }
    group.templates.push(template)
  }
  return [...byOwner.values()].sort((a, b) => {
    if (a.isYou !== b.isYou) return a.isYou ? -1 : 1
    return a.name.localeCompare(b.name)
  })
})

// autoselecciona la primera plantilla de la lista al entrar (y tras borrar)
watchEffect(() => {
  if (!store.detail && !store.loading && groups.value.length) {
    store.select(groups.value[0].templates[0].id)
  }
})

// dueño de la plantilla abierta (chip junto al título)
const detailOwner = computed(() =>
  store.detail ? travelerById(store.detail.traveler_id) : null,
)

// el admin puede REASIGNAR la plantilla a cualquier viajero desde el chip
const detailOwnerId = computed<number | null>({
  get: () => store.detail?.traveler_id ?? null,
  set: (id) => {
    if (id == null || !store.detail || id === store.detail.traveler_id) return
    store
      .reassign(store.detail.id, id)
      .catch((err) => notify.error(t('packing.toast.saveError'), err))
  },
})

// las plantillas de otros usuarios de tu familia son solo de consulta
const canEditDetail = computed(() => {
  if (!store.detail) return false
  if (session.isAdmin || store.detail.traveler_id === session.travelerId) return true
  const owner = travelerById(store.detail.traveler_id)
  return !!owner && !owner.has_user
})

const grouped = computed(() =>
  groupPackingItems(
    store.detail?.items ?? [],
    categories.packing.map((c) => c.name),
    (name) => categories.colorOf('packing', name),
  ),
)

async function createTemplate(name: string, ownerId: number) {
  try {
    const template = await store.create(name, ownerId === session.travelerId ? null : ownerId)
    await store.select(template.id)
  } catch (err) {
    notify.error(t('packing.toast.createError'), err)
  }
}

async function confirmRename() {
  if (!store.detail || !renameValue.value.trim()) return
  try {
    await store.rename(store.detail.id, renameValue.value.trim())
    renaming.value = false
  } catch (err) {
    notify.error(t('packing.toast.renameError'), err)
  }
}

function removeTemplate() {
  if (!store.detail) return
  confirmAction({
    message: t('packing.confirmRemoveTemplate.message', { name: store.detail.name }),
    header: t('packing.confirmRemoveTemplate.header'),
    accept: () => store.remove(store.detail!.id),
  })
}

async function addItem(payload: { name: string; category: string; url: string | null }) {
  if (!store.detail) return
  try {
    await store.addItem(payload)
  } catch (err) {
    notify.error(t('packing.toast.addError'), err)
    throw err // PackingAddBar conserva el texto si falla
  }
}

function saveItem(item: PackingTemplateItem, payload: { name: string; category: string; url: string | null }) {
  store.updateItem(item.id, payload)
}
</script>

<template>
  <div>
    <PageHeader
      :title="$t('packing.templatesView.title')"
      :info="$t('packing.templatesView.info')"
      class="mb-5"
    />

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
      <!-- lista de plantillas, agrupadas por dueño -->
      <TemplateList
        :groups="groups"
        :ownerOptions="ownerOptions"
        :selectedId="store.detail?.id ?? null"
        :loading="store.loading"
        @select="store.select"
        @create="createTemplate"
      />

      <!-- detalle -->
      <div class="lg:col-span-2">
        <EmptyState
          v-if="!store.detail"
          icon="pi pi-briefcase"
          :title="$t('packing.templatesView.empty.title')"
          :subtitle="$t('packing.templatesView.empty.subtitle')"
        />
        <div v-else class="bg-surface rounded-card border border-line p-5">
          <div class="flex items-center gap-2 mb-4">
            <template v-if="renaming">
              <InputText
                v-model="renameValue"
                class="flex-1"
                autofocus
                @keyup.enter="confirmRename"
                @keyup.escape="renaming = false"
              />
              <Button icon="pi pi-check" text @click="confirmRename" />
              <Button icon="pi pi-times" text severity="secondary" @click="renaming = false" />
            </template>
            <template v-else>
              <h2 class="text-lg font-semibold text-ink-heading">{{ store.detail.name }}</h2>
              <!-- dueño de la plantilla: el admin puede reasignarla a otro viajero -->
              <Select
                v-if="session.isAdmin"
                v-model="detailOwnerId"
                :options="travelers.items"
                optionLabel="name"
                optionValue="id"
                size="small"
                class="w-44"
                :aria-label="$t('packing.templates.owner')"
              >
                <template #option="{ option }">
                  <span class="flex items-center gap-2 min-w-0">
                    <span class="w-4 h-4 grid place-items-center shrink-0">
                      <TravelerAvatar
                        :name="option.name"
                        :color="option.color"
                        :avatar-url="option.avatar_url"
                        :focus-x="option.avatar_focus_x"
                        :focus-y="option.avatar_focus_y"
                        size="xs"
                      />
                    </span>
                    <span class="truncate">{{ option.name }}</span>
                  </span>
                </template>
                <template #value="{ placeholder }">
                  <span v-if="detailOwner" class="flex items-center gap-2 min-w-0">
                    <span class="w-4 h-4 grid place-items-center shrink-0">
                      <TravelerAvatar
                        :name="detailOwner.name"
                        :color="detailOwner.color"
                        :avatar-url="detailOwner.avatar_url"
                        :focus-x="detailOwner.avatar_focus_x"
                        :focus-y="detailOwner.avatar_focus_y"
                        size="xs"
                      />
                    </span>
                    <span class="truncate">{{
                      detailOwner.id === session.travelerId
                        ? $t('packing.templates.ownerYou')
                        : detailOwner.name
                    }}</span>
                  </span>
                  <span v-else>{{ placeholder }}</span>
                </template>
              </Select>
              <span
                v-else-if="detailOwner"
                class="tt-pop-in inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-surface-muted text-ink-muted"
              >
                <TravelerAvatar
                  :name="detailOwner.name"
                  :color="detailOwner.color"
                  :avatar-url="detailOwner.avatar_url"
                  :focus-x="detailOwner.avatar_focus_x"
                  :focus-y="detailOwner.avatar_focus_y"
                  size="xs"
                />
                {{ detailOwner.id === session.travelerId ? $t('packing.templates.ownerYou') : detailOwner.name }}
              </span>
              <!-- plantilla de otro usuario de tu familia: solo consulta -->
              <span
                v-if="!canEditDetail"
                class="tt-pop-in inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-surface-muted text-ink-muted"
                v-tooltip.bottom="$t('packing.templatesView.readOnlyHint')"
              >
                <i class="pi pi-lock text-3xs" /> {{ $t('packing.readOnly') }}
              </span>
              <span class="flex-1" />
              <template v-if="canEditDetail">
                <Button
                  icon="pi pi-pencil"
                  text
                  size="small"
                  severity="secondary"
                  v-tooltip.top="$t('packing.templatesView.rename')"
                  @click="renaming = true; renameValue = store.detail.name"
                />
                <Button
                  icon="pi pi-trash"
                  text
                  size="small"
                  severity="danger"
                  v-tooltip.top="$t('packing.confirmRemoveTemplate.header')"
                  @click="removeTemplate"
                />
              </template>
            </template>
          </div>

          <PackingAddBar
            v-if="canEditDetail"
            :placeholder="$t('packing.templatesView.addItemPlaceholder')"
            :categoryOptions="categoryOptions"
            :onAdd="addItem"
            class="mb-4"
          />

          <p v-if="!store.detail.items.length" class="text-sm text-ink-faint py-4 text-center">
            {{ $t('packing.templatesView.emptyTemplate') }}
          </p>

          <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4 items-start">
            <PackingCategoryCard
              v-for="group in grouped"
              :key="group.name"
              :name="group.name"
              :color="group.color"
              :count="String(group.items.length)"
              size="sm"
            >
              <TemplateItemRow
                v-for="item in group.items"
                :key="item.id"
                :item="item"
                :categoryOptions="categoryOptions"
                :readonly="!canEditDetail"
                @save="(payload) => saveItem(item, payload)"
                @remove="store.removeItem(item.id)"
              />
            </PackingCategoryCard>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
