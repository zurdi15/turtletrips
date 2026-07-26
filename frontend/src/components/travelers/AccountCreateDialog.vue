<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import Checkbox from 'primevue/checkbox'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import FormDialog from '../ui/FormDialog.vue'
import FormField from '../ui/FormField.vue'
import type { Traveler } from '../../api/types'
import { useFormDialog } from '../../composables/useFormDialog'
import { useNotify } from '../../composables/useNotify'
import { useTravelersStore } from '../../stores/travelers'
import { useUsersStore } from '../../stores/users'
import { validatePassword } from '../../utils/auth'

// da cuenta de usuario a un viajero virtual existente (solo admin)
const props = defineProps<{ traveler: Traveler | null }>()
const visible = defineModel<boolean>('visible', { required: true })

const { t } = useI18n()
const notify = useNotify()
const users = useUsersStore()
const travelers = useTravelersStore()

const username = ref('')
const password = ref('')
const confirm = ref('')
const isAdmin = ref(false)

const { saving, save } = useFormDialog({
  visible,
  entity: () => props.traveler,
  reset: () => {
    username.value = ''
    password.value = ''
    confirm.value = ''
    isAdmin.value = false
  },
  validate: () => {
    if (username.value.trim().length < 3) return t('travelers.account.invalidUsername')
    const pwError = validatePassword(password.value, confirm.value)
    return pwError ? t(`auth.password.${pwError}`) : null
  },
  submit: () =>
    users.create({
      username: username.value.trim(),
      password: password.value,
      is_admin: isAdmin.value,
      traveler_id: (props.traveler as Traveler).id,
    }),
  onSaved: () => {
    notify.success(t('travelers.account.created'))
    // has_user del viajero cambió: refrescar la lista global
    travelers.load(true)
  },
})
</script>

<template>
  <FormDialog
    v-model:visible="visible"
    :header="`${t('travelers.account.createTitle')} · ${traveler?.name ?? ''}`"
    :saving="saving"
    width="md"
    @save="save"
  >
    <FormField :label="t('travelers.account.username')" required>
      <InputText v-model="username" autocomplete="off" autofocus />
    </FormField>
    <FormField :label="t('travelers.account.password')" required>
      <Password v-model="password" :feedback="false" toggle-mask input-class="w-full" class="w-full" />
    </FormField>
    <FormField :label="t('travelers.account.confirmPassword')" required>
      <Password v-model="confirm" :feedback="false" toggle-mask input-class="w-full" class="w-full" />
    </FormField>
    <label class="flex items-center gap-2 text-sm text-ink">
      <Checkbox v-model="isAdmin" binary />
      {{ t('travelers.account.isAdmin') }}
    </label>
  </FormDialog>
</template>
