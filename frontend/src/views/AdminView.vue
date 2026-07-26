<script setup lang="ts">
import { onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import PageHeader from '../components/ui/PageHeader.vue'
import UsersPanel from '../components/admin/UsersPanel.vue'
import FamiliesPanel from '../components/admin/FamiliesPanel.vue'
import { useFamiliesStore } from '../stores/families'
import { useTravelersStore } from '../stores/travelers'
import { useUsersStore } from '../stores/users'

const { t } = useI18n()
const users = useUsersStore()
const families = useFamiliesStore()
const travelers = useTravelersStore()

onMounted(() => {
  users.load(true)
  families.load(true)
  travelers.load(true)
})
</script>

<template>
  <div class="max-w-3xl mx-auto">
    <PageHeader :title="t('admin.title')" class="mb-6" />
    <div class="flex flex-col gap-6">
      <UsersPanel />
      <FamiliesPanel />
    </div>
  </div>
</template>
