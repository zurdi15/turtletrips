<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import Password from 'primevue/password'
import FormDialog from '../ui/FormDialog.vue'
import FormField from '../ui/FormField.vue'
import type { User } from '../../api/types'
import { useFormDialog } from '../../composables/useFormDialog'
import { useNotify } from '../../composables/useNotify'
import { useUsersStore } from '../../stores/users'
import { validatePassword } from '../../utils/auth'

const props = defineProps<{ user: User | null }>()
const visible = defineModel<boolean>('visible', { required: true })

const { t } = useI18n()
const notify = useNotify()
const users = useUsersStore()

const password = ref('')
const confirm = ref('')

const { saving, save } = useFormDialog({
  visible,
  entity: () => props.user,
  reset: () => {
    password.value = ''
    confirm.value = ''
  },
  validate: () => {
    const pwError = validatePassword(password.value, confirm.value)
    return pwError ? t(`auth.password.${pwError}`) : null
  },
  submit: () => users.resetPassword((props.user as User).id, password.value),
  onSaved: () => notify.success(t('admin.users.resetDone')),
})
</script>

<template>
  <FormDialog
    v-model:visible="visible"
    :header="`${t('admin.users.resetPassword')} · ${user?.username ?? ''}`"
    :saving="saving"
    width="md"
    @save="save"
  >
    <FormField :label="t('auth.password.new')" required>
      <Password v-model="password" :feedback="false" toggle-mask input-class="w-full" class="w-full" autofocus />
    </FormField>
    <FormField :label="t('auth.password.confirm')" required>
      <Password v-model="confirm" :feedback="false" toggle-mask input-class="w-full" class="w-full" />
    </FormField>
  </FormDialog>
</template>
