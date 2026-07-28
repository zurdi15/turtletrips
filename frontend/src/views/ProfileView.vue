<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import PageHeader from '../components/ui/PageHeader.vue'
import Pill from '../components/ui/Pill.vue'
import ColorSwatchPopover from '../components/ui/ColorSwatchPopover.vue'
import ImageFramer from '../components/ui/ImageFramer.vue'
import UploadButton from '../components/ui/UploadButton.vue'
import TravelerAvatar from '../components/ui/TravelerAvatar.vue'
import type { Focus } from '../utils/imageFocus'
import PasswordChangeForm from '../components/auth/PasswordChangeForm.vue'
import { useNotify } from '../composables/useNotify'
import { useSessionStore } from '../stores/session'
import { useTravelersStore } from '../stores/travelers'
import { FALLBACK_COLOR } from '../theme'

const { t } = useI18n()
const notify = useNotify()
const session = useSessionStore()
const travelers = useTravelersStore()

const traveler = computed(() => session.me?.traveler ?? null)
const name = ref(traveler.value?.name ?? '')
watch(traveler, (v) => {
  name.value = v?.name ?? ''
})

const savingName = ref(false)
async function saveName() {
  if (!traveler.value) return
  const trimmed = name.value.trim()
  if (!trimmed || trimmed === traveler.value.name) return
  savingName.value = true
  try {
    session.setTraveler(await travelers.update(traveler.value.id, { name: trimmed }))
    notify.success(t('profile.identity.toast.saved'))
  } catch (err) {
    notify.error(t('profile.identity.toast.saveError'), err)
  } finally {
    savingName.value = false
  }
}

const colorPopover = ref<InstanceType<typeof ColorSwatchPopover>>()
async function pickColor(color: string) {
  if (!traveler.value) return
  try {
    session.setTraveler(await travelers.update(traveler.value.id, { color }))
  } catch (err) {
    notify.error(t('profile.identity.toast.saveError'), err)
  }
}

// encuadre del avatar: se guarda al soltar, no en cada píxel del arrastre
const avatarFocus = ref<Focus>({ x: 0.5, y: 0.5 })
watch(
  traveler,
  (v) => {
    avatarFocus.value = { x: v?.avatar_focus_x ?? 0.5, y: v?.avatar_focus_y ?? 0.5 }
  },
  { immediate: true },
)

async function saveAvatarFocus() {
  const current = traveler.value
  if (!current) return
  if (
    current.avatar_focus_x === avatarFocus.value.x &&
    current.avatar_focus_y === avatarFocus.value.y
  )
    return // un clic sin arrastre no manda nada
  try {
    session.setTraveler(
      await travelers.update(current.id, {
        avatar_focus_x: avatarFocus.value.x,
        avatar_focus_y: avatarFocus.value.y,
      }),
    )
  } catch (err) {
    notify.error(t('common.image.frameError'), err)
  }
}

const uploadingAvatar = ref(false)
async function onAvatar(file: File) {
  if (!traveler.value) return
  uploadingAvatar.value = true
  try {
    session.setTraveler(await travelers.uploadAvatar(traveler.value.id, file))
  } catch (err) {
    notify.error(t('profile.identity.toast.avatarError'), err)
  } finally {
    uploadingAvatar.value = false
  }
}

async function removeAvatar() {
  if (!traveler.value?.avatar_url) return
  try {
    await travelers.removeAvatar(traveler.value.id)
    session.setTraveler({ ...traveler.value, avatar_url: null })
  } catch (err) {
    notify.error(t('profile.identity.toast.saveError'), err)
  }
}
</script>

<template>
  <div class="max-w-3xl mx-auto">
    <PageHeader :title="t('profile.title')" class="mb-6" />

    <!-- las secciones entran en cascada -->
    <div v-if="session.me && traveler" class="tt-stagger flex flex-col gap-6">
      <section class="bg-surface rounded-card border border-line p-5">
        <h2 class="font-semibold text-ink mb-1">{{ t('profile.identity.title') }}</h2>
        <p class="text-xs text-ink-faint mb-4">{{ t('profile.identity.hint') }}</p>
        <div class="flex flex-col sm:flex-row gap-6 items-start">
          <div class="flex flex-col items-center gap-3">
            <!-- el key hace que cambiar la foto entre con un pop -->
            <div :key="traveler.avatar_url ?? 'none'" class="tt-pop-in">
              <!-- con foto, el círculo es arrastrable: la cara no siempre está
                   en el centro del encuadre -->
              <ImageFramer
                v-if="traveler.avatar_url"
                v-model="avatarFocus"
                :src="traveler.avatar_url"
                aspect="1 / 1"
                circle
                class="w-24"
                @pointerup="saveAvatarFocus"
                @keyup="saveAvatarFocus"
              />
              <TravelerAvatar
                v-else
                :name="traveler.name"
                :color="traveler.color"
                size="xl"
              />
            </div>
            <div class="flex gap-2">
              <UploadButton
                :label="t('profile.identity.uploadAvatar')"
                accept="image/*"
                size="small"
                severity="secondary"
                outlined
                :loading="uploadingAvatar"
                @file="onAvatar"
              />
              <Button
                v-if="traveler.avatar_url"
                :label="t('profile.identity.removeAvatar')"
                icon="pi pi-times"
                size="small"
                severity="danger"
                text
                @click="removeAvatar"
              />
            </div>
            <span v-if="traveler.avatar_url" class="text-xs text-ink-faint text-center">
              {{ t('common.image.frameHint') }}
            </span>
          </div>
          <div class="flex flex-col gap-4 flex-1 w-full">
            <div class="flex flex-col gap-1">
              <label class="text-sm font-medium">{{ t('profile.identity.name') }}</label>
              <div class="flex gap-2">
                <InputText v-model="name" class="flex-1 min-w-0" @keyup.enter="saveName" />
                <Button
                  :label="t('common.actions.save')"
                  :loading="savingName"
                  :disabled="!name.trim() || name.trim() === traveler.name"
                  @click="saveName"
                />
              </div>
            </div>
            <div class="flex items-center gap-3">
              <button
                class="w-6 h-6 rounded-full shrink-0 ring-1 ring-line hover:scale-110 transition-transform"
                :style="{ background: traveler.color ?? FALLBACK_COLOR }"
                v-tooltip.top="t('common.actions.changeColor')"
                @click="colorPopover?.toggle($event)"
              />
              <span class="text-sm text-ink-secondary">{{ t('common.actions.changeColor') }}</span>
            </div>
          </div>
        </div>
      </section>

      <section class="bg-surface rounded-card border border-line p-5">
        <h2 class="font-semibold text-ink mb-3">{{ t('profile.account.title') }}</h2>
        <dl class="flex flex-col gap-2 text-sm">
          <div class="flex items-center gap-3">
            <dt class="text-ink-muted w-24">{{ t('profile.account.username') }}</dt>
            <dd class="text-ink font-medium flex items-center gap-2">
              {{ session.me.user.username }}
              <Pill v-if="session.me.user.is_admin" color="brand" icon="pi pi-shield" pop-in>
                {{ t('profile.account.admin') }}
              </Pill>
            </dd>
          </div>
          <div class="flex items-center gap-3">
            <dt class="text-ink-muted w-24">{{ t('profile.account.family') }}</dt>
            <dd class="text-ink font-medium">
              {{ session.me.family?.name ?? t('profile.account.noFamily') }}
            </dd>
          </div>
        </dl>
      </section>

      <section class="bg-surface rounded-card border border-line p-5">
        <h2 class="font-semibold text-ink mb-1">{{ t('profile.passwordSection.title') }}</h2>
        <p class="text-xs text-ink-faint mb-4">{{ t('profile.passwordSection.hint') }}</p>
        <PasswordChangeForm />
      </section>
    </div>

    <ColorSwatchPopover ref="colorPopover" @select="pickColor" />
  </div>
</template>
