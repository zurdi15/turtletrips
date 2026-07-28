<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import ShareLinkPanel from '../../components/trip/ShareLinkPanel.vue'
import type { Trip } from '../../api/types'

const props = defineProps<{ trip: Trip }>()

const { t } = useI18n()

// la versión imprimible del enlace público sale de su propio token: aquí se
// enseña la del viaje, con gastos, que es la que solo ve quien tiene cuenta
const printTo = `/trips/${props.trip.id}/print`
</script>

<template>
  <div class="max-w-3xl mx-auto flex flex-col gap-6">
    <section class="bg-surface rounded-card border border-line p-4 sm:p-6">
      <h3 class="text-sm font-semibold text-ink-secondary">{{ t('share.section.title') }}</h3>
      <p class="text-sm text-ink-muted mt-1 mb-4">
        {{ trip.share_token ? t('share.section.active') : t('share.section.inactive') }}
      </p>
      <ShareLinkPanel :trip="trip" />
    </section>

    <section class="bg-surface rounded-card border border-line p-4 sm:p-6">
      <div class="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 class="text-sm font-semibold text-ink-secondary mb-1">{{ t('print.openTitle') }}</h3>
          <p class="text-sm text-ink-muted">{{ t('print.openHint') }}</p>
        </div>
        <router-link :to="printTo">
          <Button :label="t('print.open')" icon="pi pi-print" severity="secondary" outlined />
        </router-link>
      </div>
    </section>
  </div>
</template>
