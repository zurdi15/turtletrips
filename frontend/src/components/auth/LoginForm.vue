<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Button from 'primevue/button'
import FormField from '../ui/FormField.vue'
import { useNotify } from '../../composables/useNotify'
import { useSessionStore } from '../../stores/session'

const emit = defineEmits<{ success: [] }>()

const { t } = useI18n()
const notify = useNotify()
const session = useSessionStore()

const username = ref('')
const password = ref('')
const loading = ref(false)

async function submit() {
  if (!username.value.trim() || !password.value) return
  loading.value = true
  try {
    await session.login(username.value.trim(), password.value)
    emit('success')
  } catch (err) {
    notify.error(t('auth.login.error'), err)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <form class="flex flex-col gap-4" @submit.prevent="submit">
    <FormField :label="t('auth.login.username')" required>
      <InputText v-model="username" autocomplete="username" autofocus />
    </FormField>
    <FormField :label="t('auth.login.password')" required>
      <Password
        v-model="password"
        :feedback="false"
        toggle-mask
        autocomplete="current-password"
        input-class="w-full"
        class="w-full"
      />
    </FormField>
    <Button
      type="submit"
      :label="t('auth.login.submit')"
      :loading="loading"
      :disabled="!username.trim() || !password"
    />
  </form>
</template>
