<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import Checkbox from 'primevue/checkbox'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Select from 'primevue/select'
import FormDialog from '../ui/FormDialog.vue'
import FormField from '../ui/FormField.vue'
import { CATEGORY_PALETTE } from '../../theme'
import { useFormDialog } from '../../composables/useFormDialog'
import { useNotify } from '../../composables/useNotify'
import { useFamiliesStore } from '../../stores/families'
import { useSessionStore } from '../../stores/session'
import { useTravelersStore } from '../../stores/travelers'
import { useUsersStore } from '../../stores/users'
import { validatePassword } from '../../utils/auth'

// alta de viajero con familia y color explícitos y, para el admin, cuenta opcional
const visible = defineModel<boolean>('visible', { required: true })

const { t } = useI18n()
const notify = useNotify()
const travelers = useTravelersStore()
const families = useFamiliesStore()
const users = useUsersStore()
const session = useSessionStore()

const name = ref('')
const color = ref<string>(CATEGORY_PALETTE[0])
const familyId = ref<number | null>(null)
const withAccount = ref(false)
const username = ref('')
const password = ref('')
const confirm = ref('')
const accountAdmin = ref(false)

// un no-admin solo puede elegir su propia familia o ninguna (lo valida el backend)
const familyOptions = computed(() => {
  const none = { id: null as number | null, name: t('travelers.families.none') }
  if (session.isAdmin) return [none, ...families.items]
  const own = families.items.find((f) => f.id === session.me?.traveler.family_id)
  return own ? [none, own] : [none]
})

const { saving, save } = useFormDialog({
  visible,
  entity: () => null,
  reset: () => {
    name.value = ''
    // sugerencia rotando la paleta, como el alta rápida de siempre
    color.value = CATEGORY_PALETTE[travelers.items.length % CATEGORY_PALETTE.length]
    // sin familia por defecto: asignarla es una decisión explícita
    familyId.value = null
    withAccount.value = false
    username.value = ''
    password.value = ''
    confirm.value = ''
    accountAdmin.value = false
  },
  validate: () => {
    if (!name.value.trim()) return t('travelers.form.nameRequired')
    if (withAccount.value) {
      if (username.value.trim().length < 3) return t('travelers.account.invalidUsername')
      const pwError = validatePassword(password.value, confirm.value)
      if (pwError) return t(`auth.password.${pwError}`)
    }
    return null
  },
  submit: async () => {
    const traveler = await travelers.create(name.value.trim(), color.value, familyId.value)
    if (withAccount.value) {
      await users.create({
        username: username.value.trim(),
        password: password.value,
        is_admin: accountAdmin.value,
        traveler_id: traveler.id,
      })
    }
  },
  onSaved: () => {
    if (withAccount.value) notify.success(t('travelers.account.created'))
    // has_user / dedupe por nombre pueden cambiar la lista: refrescar
    travelers.load(true)
  },
})
</script>

<template>
  <FormDialog
    v-model:visible="visible"
    :header="t('travelers.form.title')"
    :saving="saving"
    width="md"
    @save="save"
  >
    <FormField :label="t('travelers.form.name')" required>
      <InputText v-model="name" autofocus @keyup.enter="save" />
    </FormField>
    <FormField :label="t('travelers.form.color')">
      <div class="flex flex-wrap gap-2 pt-1">
        <button
          v-for="swatch in CATEGORY_PALETTE"
          :key="swatch"
          type="button"
          class="w-6 h-6 rounded-full transition-transform hover:scale-110"
          :class="color === swatch ? 'ring-2 ring-offset-2 ring-primary scale-110' : 'ring-1 ring-line'"
          :style="{ background: swatch }"
          @click="color = swatch"
        />
      </div>
    </FormField>
    <FormField :label="t('travelers.form.family')">
      <Select v-model="familyId" :options="familyOptions" option-label="name" option-value="id" />
    </FormField>

    <template v-if="session.isAdmin">
      <label class="flex items-center gap-2 text-sm text-ink">
        <Checkbox v-model="withAccount" binary />
        {{ t('travelers.form.createAccount') }}
      </label>
      <!-- los campos de cuenta entran con un rise suave al marcar la casilla -->
      <Transition name="tt-rise">
        <div v-if="withAccount" class="flex flex-col gap-4">
          <FormField :label="t('travelers.account.username')" required>
            <InputText v-model="username" autocomplete="off" />
          </FormField>
          <div class="grid sm:grid-cols-2 gap-4">
            <FormField :label="t('travelers.account.password')" required>
              <Password v-model="password" :feedback="false" toggle-mask input-class="w-full" class="w-full" />
            </FormField>
            <FormField :label="t('travelers.account.confirmPassword')" required>
              <Password v-model="confirm" :feedback="false" toggle-mask input-class="w-full" class="w-full" />
            </FormField>
          </div>
          <label class="flex items-center gap-2 text-sm text-ink">
            <Checkbox v-model="accountAdmin" binary />
            {{ t('travelers.account.isAdmin') }}
          </label>
        </div>
      </Transition>
    </template>
  </FormDialog>
</template>
