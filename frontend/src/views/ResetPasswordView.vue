<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import ProgressSpinner from 'primevue/progressspinner'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import AuthCard from '../components/auth/AuthCard.vue'
import ResetPasswordForm from '../components/auth/ResetPasswordForm.vue'
import FormField from '../components/ui/FormField.vue'
import { useNotify } from '../composables/useNotify'
import { useSessionStore } from '../stores/session'
import { extractResetToken } from '../utils/auth'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const notify = useNotify()
const session = useSessionStore()

// el enlace del admin trae el token en la URL; sin él se puede pegar a mano
// (por chat llega tan a menudo partido como entero)
const pasted = ref('')
const manual = ref('')
const token = computed(() =>
  typeof route.query.token === 'string' && route.query.token
    ? route.query.token
    : manual.value,
)

const username = ref<string | null>(null)
const checking = ref(false)
const invalid = ref(false)

// validar ANTES de pedir la contraseña: un enlace caducado se dice de frente
// en vez de esperar a que falle el envío
watch(
  token,
  async (value) => {
    username.value = null
    invalid.value = false
    if (!value) return
    checking.value = true
    try {
      username.value = (await session.checkResetToken(value)).username
    } catch {
      invalid.value = true
    } finally {
      checking.value = false
    }
  },
  { immediate: true },
)

function usePasted() {
  const value = extractResetToken(pasted.value)
  if (value) manual.value = value
}

function startOver() {
  manual.value = ''
  pasted.value = ''
  if (route.query.token) router.replace({ name: 'reset-password' })
}

function onSuccess() {
  // la respuesta del reset ya trae la sesión abierta: directo a los viajes
  notify.success(t('auth.reset.done'))
  router.replace('/')
}
</script>

<template>
  <AuthCard :title="t('auth.reset.title')">
    <Transition name="tt-fade" mode="out-in">
      <div v-if="checking" key="checking" class="flex flex-col items-center gap-3 py-6">
        <ProgressSpinner class="w-10 h-10" stroke-width="4" />
        <p class="text-sm text-ink-muted">{{ t('auth.reset.checking') }}</p>
      </div>

      <div v-else-if="invalid" key="invalid" class="flex flex-col gap-4">
        <div
          class="tt-pop-in rounded-card border border-warn-tint-strong bg-warn-tint p-4 flex gap-3"
        >
          <i class="pi pi-exclamation-triangle text-warn-strong mt-0.5" />
          <div class="flex flex-col gap-1">
            <p class="text-sm font-semibold text-ink-heading">
              {{ t('auth.reset.invalid.title') }}
            </p>
            <p class="text-sm text-ink-secondary">{{ t('auth.reset.invalid.body') }}</p>
          </div>
        </div>
        <Button :label="t('auth.reset.invalid.paste')" outlined @click="startOver" />
        <Button
          :label="t('auth.reset.invalid.retry')"
          @click="router.push({ name: 'forgot-password' })"
        />
      </div>

      <ResetPasswordForm
        v-else-if="username"
        key="form"
        :token="token"
        :username="username"
        @success="onSuccess"
      />

      <form v-else key="paste" class="tt-stagger flex flex-col gap-4" @submit.prevent="usePasted">
        <p class="text-sm text-ink-secondary">{{ t('auth.reset.paste.hint') }}</p>
        <FormField :label="t('auth.reset.paste.label')" required>
          <InputText v-model="pasted" autofocus />
        </FormField>
        <Button
          type="submit"
          :label="t('auth.reset.paste.submit')"
          :disabled="!pasted.trim()"
        />
      </form>
    </Transition>
    <Button
      :label="t('auth.forgot.back')"
      text
      size="small"
      icon="pi pi-arrow-left"
      @click="router.push({ name: 'login' })"
    />
  </AuthCard>
</template>
