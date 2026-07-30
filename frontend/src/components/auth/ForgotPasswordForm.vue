<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import FormField from '../ui/FormField.vue'
import { useNotify } from '../../composables/useNotify'
import { useSessionStore } from '../../stores/session'

// Los campos entran en cascada al montarse (tt-stagger).
// ⚠️ La plantilla empieza DIRECTAMENTE por el <form>: en dev los comentarios
// de raíz cuentan como nodo y el componente pasa a ser un fragmento — dentro
// de un <Transition mode="out-in"> su salida no termina nunca y el aviso
// siguiente se queda sin montar.
const emit = defineEmits<{ sent: [] }>()

const { t } = useI18n()
const notify = useNotify()
const session = useSessionStore()

const username = ref('')
const loading = ref(false)

async function submit() {
  if (!username.value.trim()) return
  loading.value = true
  try {
    await session.requestPasswordReset(username.value.trim())
    emit('sent')
  } catch (err) {
    notify.error(t('auth.forgot.error'), err)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <form class="tt-stagger flex flex-col gap-4" @submit.prevent="submit">
    <p class="text-sm text-ink-secondary">{{ t('auth.forgot.hint') }}</p>
    <FormField :label="t('auth.login.username')" required>
      <InputText v-model="username" autocomplete="username" autofocus />
    </FormField>
    <Button
      type="submit"
      :label="t('auth.forgot.submit')"
      :loading="loading"
      :disabled="!username.trim()"
    />
  </form>
</template>
