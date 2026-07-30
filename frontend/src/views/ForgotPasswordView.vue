<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import Button from 'primevue/button'
import AuthCard from '../components/auth/AuthCard.vue'
import ForgotPasswordForm from '../components/auth/ForgotPasswordForm.vue'

const { t } = useI18n()
const router = useRouter()

// la respuesta es la misma exista o no la cuenta (el backend no lo cuenta):
// el aviso habla del enlace "si la cuenta existe"
const sent = ref(false)
</script>

<template>
  <AuthCard :title="t('auth.forgot.title')">
    <Transition name="tt-fade" mode="out-in">
      <ForgotPasswordForm v-if="!sent" key="form" @sent="sent = true" />
      <div v-else key="sent" class="flex flex-col gap-4">
        <div
          class="tt-pop-in rounded-card border border-brand-tint-strong bg-brand-tint p-4 flex gap-3"
        >
          <i class="pi pi-server text-brand-strong mt-0.5" />
          <div class="flex flex-col gap-1">
            <p class="text-sm font-semibold text-ink-heading">
              {{ t('auth.forgot.sent.title') }}
            </p>
            <p class="text-sm text-ink-secondary">{{ t('auth.forgot.sent.body') }}</p>
          </div>
        </div>
        <Button
          :label="t('auth.forgot.sent.hasLink')"
          outlined
          @click="router.push({ name: 'reset-password' })"
        />
      </div>
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
