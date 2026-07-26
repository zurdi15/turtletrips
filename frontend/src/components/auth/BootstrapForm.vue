<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Button from 'primevue/button'
import FormField from '../ui/FormField.vue'
import { useNotify } from '../../composables/useNotify'
import { useSessionStore } from '../../stores/session'
import { validatePassword } from '../../utils/auth'

const emit = defineEmits<{ success: [] }>()

const { t } = useI18n()
const notify = useNotify()
const session = useSessionStore()

const username = ref('')
const password = ref('')
const confirm = ref('')
const travelerName = ref('')
const loading = ref(false)

const passwordError = computed(() => {
  if (!password.value && !confirm.value) return null
  return validatePassword(password.value, confirm.value)
})
const valid = computed(
  () =>
    username.value.trim().length >= 3 &&
    travelerName.value.trim().length > 0 &&
    validatePassword(password.value, confirm.value) === null,
)

async function submit() {
  if (!valid.value) return
  loading.value = true
  try {
    await session.bootstrap({
      username: username.value.trim(),
      password: password.value,
      traveler_name: travelerName.value.trim(),
    })
    emit('success')
  } catch (err) {
    notify.error(t('auth.bootstrap.error'), err)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <form class="flex flex-col gap-4" @submit.prevent="submit">
    <p class="text-sm text-ink-secondary">{{ t('auth.bootstrap.hint') }}</p>
    <FormField :label="t('auth.login.username')" required>
      <InputText v-model="username" autocomplete="username" autofocus />
    </FormField>
    <FormField :label="t('auth.bootstrap.travelerName')" required>
      <InputText v-model="travelerName" />
    </FormField>
    <FormField :label="t('auth.login.password')" required>
      <Password
        v-model="password"
        :feedback="false"
        toggle-mask
        autocomplete="new-password"
        input-class="w-full"
        class="w-full"
      />
    </FormField>
    <FormField :label="t('auth.bootstrap.confirmPassword')" required>
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
    <Button type="submit" :label="t('auth.bootstrap.submit')" :loading="loading" :disabled="!valid" />
  </form>
</template>
