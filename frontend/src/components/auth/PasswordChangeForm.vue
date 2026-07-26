<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import Password from 'primevue/password'
import Button from 'primevue/button'
import FormField from '../ui/FormField.vue'
import { useNotify } from '../../composables/useNotify'
import { useSessionStore } from '../../stores/session'
import { validatePassword } from '../../utils/auth'

const { t } = useI18n()
const notify = useNotify()
const session = useSessionStore()

const current = ref('')
const password = ref('')
const confirm = ref('')
const saving = ref(false)

const passwordError = computed(() => {
  if (!password.value && !confirm.value) return null
  return validatePassword(password.value, confirm.value)
})
const valid = computed(
  () => current.value.length > 0 && validatePassword(password.value, confirm.value) === null,
)

async function submit() {
  if (!valid.value) return
  saving.value = true
  try {
    await session.changePassword(current.value, password.value)
    notify.success(t('auth.password.changed'))
    current.value = ''
    password.value = ''
    confirm.value = ''
  } catch (err) {
    notify.error(t('auth.password.changeError'), err)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <form class="flex flex-col gap-4 max-w-sm" @submit.prevent="submit">
    <FormField :label="t('auth.password.current')" required>
      <Password
        v-model="current"
        :feedback="false"
        toggle-mask
        autocomplete="current-password"
        input-class="w-full"
        class="w-full"
      />
    </FormField>
    <FormField :label="t('auth.password.new')" required>
      <Password
        v-model="password"
        :feedback="false"
        toggle-mask
        autocomplete="new-password"
        input-class="w-full"
        class="w-full"
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
    <div>
      <Button type="submit" :label="t('auth.password.change')" :loading="saving" :disabled="!valid" />
    </div>
  </form>
</template>
