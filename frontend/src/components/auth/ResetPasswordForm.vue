<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import Password from 'primevue/password'
import Button from 'primevue/button'
import FormField from '../ui/FormField.vue'
import { useNotify } from '../../composables/useNotify'
import { useSessionStore } from '../../stores/session'
import { validatePassword } from '../../utils/auth'

// Los campos entran en cascada al montarse (tt-stagger); la plantilla empieza
// por el <form> sin comentario delante (ver nota en ForgotPasswordForm).
const props = defineProps<{ token: string; username: string }>()
const emit = defineEmits<{ success: [] }>()

const { t } = useI18n()
const notify = useNotify()
const session = useSessionStore()

const password = ref('')
const confirm = ref('')
const loading = ref(false)

const passwordError = computed(() => {
  if (!password.value && !confirm.value) return null
  return validatePassword(password.value, confirm.value)
})
const valid = computed(() => validatePassword(password.value, confirm.value) === null)

async function submit() {
  if (!valid.value) return
  loading.value = true
  try {
    await session.resetPassword(props.token, password.value)
    emit('success')
  } catch (err) {
    notify.error(t('auth.reset.error'), err)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <form class="tt-stagger flex flex-col gap-4" @submit.prevent="submit">
    <p class="text-sm text-ink-secondary">
      {{ t('auth.reset.forUser', { username }) }}
    </p>
    <!-- el gestor de contraseñas necesita saber a qué cuenta pertenece la nueva -->
    <input type="text" autocomplete="username" :value="username" hidden readonly />
    <FormField :label="t('auth.password.new')" required>
      <Password
        v-model="password"
        :feedback="false"
        toggle-mask
        autocomplete="new-password"
        input-class="w-full"
        class="w-full"
        autofocus
      />
    </FormField>
    <FormField :label="t('auth.password.confirm')" required>
      <Password
        v-model="confirm"
        :feedback="false"
        toggle-mask
        autocomplete="new-password"
        input-class="w-full"
        class="w-full"
      />
      <template #hint>
        <small v-if="passwordError" class="text-red-600">
          {{ t(`auth.password.${passwordError}`) }}
        </small>
      </template>
    </FormField>
    <Button
      type="submit"
      :label="t('auth.reset.submit')"
      :loading="loading"
      :disabled="!valid"
    />
  </form>
</template>
