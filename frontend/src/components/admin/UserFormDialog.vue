<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Select from 'primevue/select'
import Checkbox from 'primevue/checkbox'
import FormDialog from '../ui/FormDialog.vue'
import FormField from '../ui/FormField.vue'
import ClusterBtn from '../ui/ClusterBtn.vue'
import type { UserCreateInput } from '../../api/types'
import { useFormDialog } from '../../composables/useFormDialog'
import { useNotify } from '../../composables/useNotify'
import { useFamiliesStore } from '../../stores/families'
import { useTravelersStore } from '../../stores/travelers'
import { useUsersStore } from '../../stores/users'
import { validatePassword } from '../../utils/auth'

const visible = defineModel<boolean>('visible', { required: true })

const { t } = useI18n()
const notify = useNotify()
const users = useUsersStore()
const families = useFamiliesStore()
const travelers = useTravelersStore()

const username = ref('')
const password = ref('')
const confirm = ref('')
const mode = ref<'link' | 'create'>('create')
const travelerId = ref<number | null>(null)
const travelerName = ref('')
const familyId = ref<number | null>(null)
const isAdmin = ref(false)

// solo se pueden vincular viajeros virtuales (sin cuenta previa)
const freeTravelers = computed(() => travelers.items.filter((tr) => !tr.has_user))
const modeOptions = computed(
  () =>
    [
      { value: 'link', label: t('admin.users.linkExisting') },
      { value: 'create', label: t('admin.users.createNew') },
    ] as const,
)
const familyOptions = computed(() => [
  { id: null as number | null, name: t('admin.users.noFamily') },
  ...families.items,
])

const { saving, save } = useFormDialog({
  visible,
  entity: () => null,
  reset: () => {
    username.value = ''
    password.value = ''
    confirm.value = ''
    mode.value = freeTravelers.value.length ? 'link' : 'create'
    travelerId.value = null
    travelerName.value = ''
    familyId.value = null
    isAdmin.value = false
  },
  validate: () => {
    if (username.value.trim().length < 3) return t('admin.users.invalidUsername')
    const pwError = validatePassword(password.value, confirm.value)
    if (pwError) return t(`auth.password.${pwError}`)
    if (mode.value === 'link' && travelerId.value === null) return t('admin.users.travelerRequired')
    if (mode.value === 'create' && !travelerName.value.trim()) return t('admin.users.travelerRequired')
    return null
  },
  submit: () => {
    const payload: UserCreateInput = {
      username: username.value.trim(),
      password: password.value,
      is_admin: isAdmin.value,
      family_id: familyId.value,
      ...(mode.value === 'link'
        ? { traveler_id: travelerId.value as number }
        : { traveler_name: travelerName.value.trim() }),
    }
    return users.create(payload)
  },
  onSaved: () => {
    notify.success(t('admin.users.toast.created'))
    // el viajero vinculado/creado cambió: refrescar la lista global
    travelers.load(true)
  },
})
</script>

<template>
  <FormDialog v-model:visible="visible" :header="t('admin.users.new')" :saving="saving" @save="save">
    <FormField :label="t('admin.users.username')" required>
      <InputText v-model="username" autocomplete="off" autofocus />
    </FormField>
    <div class="grid sm:grid-cols-2 gap-4">
      <FormField :label="t('admin.users.password')" required>
        <Password v-model="password" :feedback="false" toggle-mask input-class="w-full" class="w-full" />
      </FormField>
      <FormField :label="t('admin.users.confirmPassword')" required>
        <Password v-model="confirm" :feedback="false" toggle-mask input-class="w-full" class="w-full" />
      </FormField>
    </div>
    <FormField :label="t('admin.users.traveler')" required>
      <div class="flex flex-col gap-2">
        <ClusterBtn v-model="mode" :options="modeOptions" size="small" />
        <Select
          v-if="mode === 'link'"
          v-model="travelerId"
          :options="freeTravelers"
          option-label="name"
          option-value="id"
          :placeholder="t('admin.users.freeTravelers')"
          filter
        />
        <InputText v-else v-model="travelerName" :placeholder="t('admin.users.travelerName')" />
      </div>
    </FormField>
    <FormField :label="t('admin.users.family')">
      <Select v-model="familyId" :options="familyOptions" option-label="name" option-value="id" />
    </FormField>
    <label class="flex items-center gap-2 text-sm text-ink">
      <Checkbox v-model="isAdmin" binary />
      {{ t('admin.users.isAdmin') }}
    </label>
  </FormDialog>
</template>
