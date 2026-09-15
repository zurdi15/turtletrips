<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import draggable from 'vuedraggable'
import Button from 'primevue/button'
import EmptyState from '../../components/EmptyState.vue'
import TabSkeleton from '../../components/TabSkeleton.vue'
import LinkDialog from '../../components/links/LinkDialog.vue'
import LinkGroupDialog from '../../components/links/LinkGroupDialog.vue'
import LinkGroupSection from '../../components/links/LinkGroupSection.vue'
import type { LinkGroup, Trip, TripLink } from '../../api/types'
import { useLinksStore } from '../../stores/links'
import { useLinkGroupsStore } from '../../stores/linkGroups'
import { useConfirmDelete } from '../../composables/useConfirmDelete'
import { useCrudView } from '../../composables/useCrudView'
import { useNotify } from '../../composables/useNotify'
import { useTripTabData } from '../../composables/useTripTabData'
import { NO_GROUP_KEY, bucketKey, bucketsFromLists, groupLinks } from '../../utils/links'

const props = defineProps<{ trip: Trip }>()
const { t } = useI18n()
const links = useLinksStore()
const groups = useLinkGroupsStore()
const notify = useNotify()
const confirmAction = useConfirmDelete()

useTripTabData(() => props.trip, {
  load(tripId) {
    links.load(tripId)
    groups.load(tripId)
  },
})

const initialLoading = computed(
  () => (links.loading || groups.loading) && !links.items.length && !groups.items.length,
)
const isEmpty = computed(() => !links.items.length && !groups.items.length)

// espejos locales para los dos <draggable> (bloques y enlaces por cubo): el
// drag reordena en sitio y luego se persiste la disposición entera
const groupList = ref<LinkGroup[]>([])
const lists = reactive<Record<string, TripLink[]>>({})

watch(
  [() => groups.items, () => links.items],
  () => {
    const sections = groupLinks(groups.items, links.items)
    groupList.value = sections.flatMap((s) => (s.group ? [s.group] : []))
    for (const key of Object.keys(lists)) delete lists[key]
    for (const s of sections) lists[bucketKey(s.group?.id ?? null)] = s.links
  },
  { immediate: true, deep: true },
)

// "sin bloque": único cubo (sin cabecera) mientras no hay bloques; con
// bloques solo aparece si tiene algo, para no dejar una caja vacía perpetua
const showUngrouped = computed(
  () => !groupList.value.length || (lists[NO_GROUP_KEY]?.length ?? 0) > 0,
)

async function persistLinkOrder() {
  try {
    await links.reorder(bucketsFromLists(lists))
  } catch (err) {
    notify.error(t('links.toast.reorderError'), err)
    links.load(props.trip.id)
  }
}

async function persistGroupOrder() {
  const ids = groupList.value.map((g) => g.id)
  try {
    await groups.reorder(ids)
    // espejo en el store: groupLinks ordena por position
    for (const g of groups.items) g.position = ids.indexOf(g.id)
  } catch (err) {
    notify.error(t('links.toast.reorderError'), err)
    groups.load(props.trip.id)
  }
}

// ---- enlaces ----

const defaultGroupId = ref<number | null>(null)

const { showForm, editing, openNew, openEdit, removeItem } = useCrudView<TripLink>({
  confirm: (link) => ({
    message: t('links.confirm.message', { name: link.title }),
    header: t('links.confirm.header'),
  }),
  remove: (link) => links.remove(link.id),
})

function openNewIn(groupId: number | null) {
  defaultGroupId.value = groupId
  openNew()
}

// reintento de miniatura (uno a la vez: el servidor tarda lo que tarde la web)
const refreshingId = ref<number | null>(null)

async function refreshImage(link: TripLink) {
  if (refreshingId.value !== null) return
  refreshingId.value = link.id
  try {
    const found = await links.refreshImage(link.id)
    if (found) notify.success(t('links.toast.imageUpdated'))
    else notify.info(t('links.toast.noImage'), t('links.toast.noImageDetail'))
  } catch (err) {
    notify.error(t('links.toast.imageError'), err)
  } finally {
    refreshingId.value = null
  }
}

// ---- bloques ----

const showGroupForm = ref(false)
const editingGroup = ref<LinkGroup | null>(null)

function openGroupForm(group: LinkGroup | null) {
  editingGroup.value = group
  showGroupForm.value = true
}

// modo Ordenar: las asas del drag & drop solo aparecen mientras está activo
const reordering = ref(false)

function removeGroup(group: LinkGroup) {
  confirmAction({
    message: t('links.confirm.groupMessage', { name: group.name }),
    header: t('links.confirm.groupHeader'),
    async accept() {
      try {
        await groups.remove(group.id)
        links.detachGroup(group.id)
      } catch (err) {
        notify.error(t('links.toast.deleteError'), err)
      }
    },
  })
}
</script>

<template>
  <div>
    <div class="flex flex-col sm:flex-row sm:items-center gap-2 mb-4">
      <Button
        :label="$t('links.newLink')"
        icon="pi pi-plus"
        class="w-full sm:w-auto"
        @click="openNewIn(null)"
      />
      <Button
        :label="$t('links.newGroup')"
        icon="pi pi-folder-plus"
        outlined
        severity="secondary"
        class="w-full sm:w-auto"
        @click="openGroupForm(null)"
      />
      <Button
        v-if="!isEmpty"
        :label="reordering ? $t('links.reorderDone') : $t('links.reorder')"
        :icon="reordering ? 'pi pi-check' : 'pi pi-sort-alt'"
        :outlined="!reordering"
        severity="secondary"
        class="w-full sm:w-auto sm:ml-auto"
        @click="reordering = !reordering"
      />
    </div>
    <p v-if="reordering" class="text-xs text-ink-faint -mt-2 mb-4">
      {{ $t('links.reorderHint') }}
    </p>

    <TabSkeleton v-if="initialLoading" variant="list" :rows="6" />

    <EmptyState
      v-else-if="isEmpty"
      icon="pi pi-link"
      :title="t('links.empty.title')"
      :subtitle="t('links.empty.subtitle')"
    />

    <div v-else class="flex flex-col gap-4">
      <!-- bloques: cascada al montar y drag & drop por el asa de la cabecera -->
      <draggable
        :list="groupList"
        item-key="id"
        handle=".tt-group-handle"
        :disabled="!reordering"
        group="link-groups"
        ghost-class="opacity-40"
        tag="div"
        class="tt-stagger flex flex-col gap-4 empty:hidden"
        @end="persistGroupOrder"
      >
        <template #item="{ element }">
          <LinkGroupSection
            :group="element"
            :links="lists[bucketKey(element.id)] ?? []"
            :reorderable="reordering"
            :refreshingId="refreshingId"
            @edit="openGroupForm(element)"
            @remove="removeGroup(element)"
            @add="openNewIn(element.id)"
            @edit-link="openEdit"
            @remove-link="removeItem"
            @refresh-image="refreshImage"
            @reorder="persistLinkOrder"
          />
        </template>
      </draggable>

      <LinkGroupSection
        v-if="showUngrouped"
        :group="null"
        :links="lists[NO_GROUP_KEY] ?? []"
        :bare="!groupList.length"
        :reorderable="reordering"
        :refreshingId="refreshingId"
        @add="openNewIn(null)"
        @edit-link="openEdit"
        @remove-link="removeItem"
        @refresh-image="refreshImage"
        @reorder="persistLinkOrder"
      />
    </div>

    <LinkDialog v-model:visible="showForm" :link="editing" :defaultGroupId="defaultGroupId" />
    <LinkGroupDialog v-model:visible="showGroupForm" :group="editingGroup" />
  </div>
</template>
