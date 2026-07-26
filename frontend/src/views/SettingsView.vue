<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import ClusterBtn from '../components/ui/ClusterBtn.vue'
import PageHeader from '../components/ui/PageHeader.vue'
import EditableListItem from '../components/ui/EditableListItem.vue'
import ColorSwatchPopover from '../components/ui/ColorSwatchPopover.vue'
import UploadButton from '../components/ui/UploadButton.vue'
import { api, API_BASE } from '../api/client'
import type { Category, ThemePref } from '../api/types'
import { CATEGORY_PALETTE } from '../theme'
import { useCategoriesStore, FALLBACK_CATEGORY_COLOR } from '../stores/categories'
import { useSessionStore } from '../stores/session'
import { useConfirmDelete } from '../composables/useConfirmDelete'
import { useNotify } from '../composables/useNotify'
import { useTheme } from '../composables/useTheme'
import { useI18n } from 'vue-i18n'
import { setLocale, type AppLocale } from '../i18n'

const categories = useCategoriesStore()
const session = useSessionStore()
const confirmAction = useConfirmDelete()
const notify = useNotify()
const { t, locale } = useI18n()

// tema e idioma se aplican en local al instante y se persisten en la cuenta
// (best-effort: si el PATCH falla, la preferencia local sigue valiendo)
function persistSettings(patch: { theme?: ThemePref; language?: AppLocale }) {
  session.updateSettings(patch).catch((err) => {
    notify.error(t('settings.toast.saveError'), err)
  })
}

// ---- idioma ----

const language = computed<AppLocale>({
  get: () => locale.value as AppLocale,
  set: (v) => {
    setLocale(v)
    persistSettings({ language: v })
  },
})
// endónimos: el nombre de cada idioma no se traduce
const languageOptions = [
  { value: 'es', label: 'Español' },
  { value: 'en', label: 'English' },
] as const

// ---- apariencia (claro/oscuro/sistema) ----

const { themePref, setThemePref } = useTheme()
const theme = computed<ThemePref>({
  get: () => themePref.value,
  set: (v) => {
    setThemePref(v)
    persistSettings({ theme: v })
  },
})
const themeOptions = computed(
  () =>
    [
      { value: 'light', label: t('settings.appearance.light'), icon: 'pi pi-sun' },
      { value: 'dark', label: t('settings.appearance.dark'), icon: 'pi pi-moon' },
      { value: 'system', label: t('settings.appearance.system'), icon: 'pi pi-desktop' },
    ] as const,
)

// ---- copia de seguridad ----

const backupExportUrl = `${API_BASE}/backup/export`
const restoring = ref(false)

function onRestoreFilePicked(file: File) {
  confirmAction({
    message: t('settings.backup.confirm.message'),
    header: t('settings.backup.confirm.header'),
    acceptLabel: t('settings.backup.confirm.accept'),
    accept: async () => {
      restoring.value = true
      try {
        const form = new FormData()
        form.append('file', file)
        const result = await api.upload<{ trips: number }>('/backup/restore', form)
        notify.success(t('settings.backup.toast.restored', { n: result.trips }))
        // todas las stores quedan obsoletas tras el restore
        setTimeout(() => window.location.reload(), 800)
      } catch (err) {
        notify.error(t('settings.backup.toast.restoreError'), err)
        restoring.value = false
      }
    },
  })
}

onMounted(() => {
  categories.load('expense')
  categories.load('packing')
})

const newNames = ref<Record<string, string>>({ expense: '', packing: '' })

const colorTarget = ref<{ kind: 'expense' | 'packing'; id: number } | null>(null)
const colorPopover = ref<InstanceType<typeof ColorSwatchPopover>>()

function openColorPicker(event: Event, kind: 'expense' | 'packing', id: number) {
  colorTarget.value = { kind, id }
  colorPopover.value?.toggle(event)
}

async function pickColor(color: string) {
  if (!colorTarget.value) return
  try {
    await categories.update(colorTarget.value.id, colorTarget.value.kind, { color })
  } catch (err) {
    notify.error(t('settings.categories.toast.colorError'), err)
  }
}

async function addCategory(kind: 'expense' | 'packing') {
  const name = newNames.value[kind].trim()
  if (!name) return
  try {
    const color = CATEGORY_PALETTE[categories[kind].length % CATEGORY_PALETTE.length]
    await categories.create(kind, name, color)
    newNames.value[kind] = ''
  } catch (err) {
    notify.error(t('settings.categories.toast.addError'), err)
  }
}

async function renameCategory(kind: 'expense' | 'packing', category: Category, name: string) {
  try {
    await categories.update(category.id, kind, { name })
  } catch (err) {
    notify.error(t('settings.categories.toast.renameError'), err)
  }
}

function removeCategory(kind: 'expense' | 'packing', category: Category) {
  confirmAction({
    message: t('settings.categories.confirmDelete.message', { name: category.name }),
    header: t('settings.categories.confirmDelete.header'),
    accept: () => categories.remove(category.id, kind),
  })
}

const sections = computed<{ kind: 'expense' | 'packing'; title: string; hint: string }[]>(() => [
  {
    kind: 'expense',
    title: t('settings.categories.expense.title'),
    hint: t('settings.categories.expense.hint'),
  },
  {
    kind: 'packing',
    title: t('settings.categories.packing.title'),
    hint: t('settings.categories.packing.hint'),
  },
])
</script>

<template>
  <div class="max-w-3xl mx-auto">
    <PageHeader :title="t('settings.title')" class="mb-6" />

    <div class="flex flex-col gap-6">
      <section class="bg-surface rounded-card border border-line p-5">
        <h2 class="font-semibold text-ink mb-1">{{ t('settings.appearance.title') }}</h2>
        <p class="text-xs text-ink-faint mb-4">{{ t('settings.appearance.hint') }}</p>
        <ClusterBtn v-model="theme" :options="themeOptions" :aria-label="t('settings.appearance.title')" />
      </section>

      <section class="bg-surface rounded-card border border-line p-5">
        <h2 class="font-semibold text-ink mb-1">{{ t('settings.language.title') }}</h2>
        <p class="text-xs text-ink-faint mb-4">{{ t('settings.language.hint') }}</p>
        <ClusterBtn v-model="language" :options="languageOptions" :aria-label="t('settings.language.title')" />
      </section>

      <section
        v-for="section in sections"
        :key="section.kind"
        class="bg-surface rounded-card border border-line p-5"
      >
        <h2 class="font-semibold text-ink mb-1">{{ section.title }}</h2>
        <p class="text-xs text-ink-faint mb-4">{{ section.hint }}</p>
        <ul class="flex flex-col gap-1.5 mb-4">
          <EditableListItem
            v-for="category in categories[section.kind]"
            :key="category.id"
            :name="category.name"
            :color="category.color"
            :colorFallback="FALLBACK_CATEGORY_COLOR"
            @rename="(name) => renameCategory(section.kind, category, name)"
            @remove="removeCategory(section.kind, category)"
            @pick-color="(event) => openColorPicker(event, section.kind, category.id)"
          />
        </ul>
        <div class="flex gap-2">
          <InputText
            v-model="newNames[section.kind]"
            :placeholder="t('settings.categories.newPlaceholder')"
            class="flex-1 min-w-0"
            @keyup.enter="addCategory(section.kind)"
          />
          <Button
            :label="t('common.actions.add')"
            icon="pi pi-plus"
            class="shrink-0 max-sm:[&_.p-button-label]:hidden"
            @click="addCategory(section.kind)"
          />
        </div>
      </section>

      <section v-if="session.isAdmin" class="bg-surface rounded-card border border-line p-5">
        <h2 class="font-semibold text-ink mb-1">{{ t('settings.backup.title') }}</h2>
        <p class="text-xs text-ink-faint mb-4">
          {{ t('settings.backup.hint') }}
        </p>
        <div class="flex flex-wrap gap-2">
          <a :href="backupExportUrl" download>
            <Button
              :label="t('settings.backup.download')"
              icon="pi pi-download"
              severity="secondary"
              outlined
            />
          </a>
          <UploadButton
            :label="t('settings.backup.restore')"
            icon="pi pi-upload"
            severity="danger"
            outlined
            accept=".zip,application/zip"
            :loading="restoring"
            @file="onRestoreFilePicked"
          />
        </div>
      </section>
    </div>

    <ColorSwatchPopover ref="colorPopover" @select="pickColor" />
  </div>
</template>
