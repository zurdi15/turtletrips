<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import InputText from 'primevue/inputtext'
import FormDialog from '../ui/FormDialog.vue'
import FormField from '../ui/FormField.vue'
import type { LinkGroup } from '../../api/types'
import { LINK_GROUP_ICONS } from '../../constants'
import { useLinkGroupsStore } from '../../stores/linkGroups'
import { useFormDialog } from '../../composables/useFormDialog'

const props = defineProps<{ group: LinkGroup | null }>()
const visible = defineModel<boolean>('visible', { required: true })
const { t } = useI18n()
const store = useLinkGroupsStore()

const name = ref('')
const icon = ref<string>(LINK_GROUP_ICONS[0])

const { saving, save } = useFormDialog<LinkGroup>({
  visible,
  entity: () => props.group,
  reset(group) {
    name.value = group?.name ?? ''
    icon.value = group?.icon ?? LINK_GROUP_ICONS[0]
  },
  validate: () => (name.value.trim() ? null : t('links.groupDialog.nameRequired')),
  submit() {
    const payload = { name: name.value.trim(), icon: icon.value }
    return props.group ? store.update(props.group.id, payload) : store.create(payload)
  },
})
</script>

<template>
  <FormDialog
    v-model:visible="visible"
    :header="group ? $t('links.groupDialog.editTitle') : $t('links.groupDialog.newTitle')"
    :saving="saving"
    width="md"
    @save="save"
  >
    <FormField :label="$t('links.groupDialog.name')" required>
      <InputText
        v-model="name"
        autofocus
        :placeholder="$t('links.groupDialog.namePlaceholder')"
        @keyup.enter="save"
      />
    </FormField>
    <FormField :label="$t('links.groupDialog.icon')">
      <!-- rejilla de iconos: el elegido lleva el anillo de selección -->
      <div class="grid grid-cols-8 gap-1.5">
        <button
          v-for="name in LINK_GROUP_ICONS"
          :key="name"
          type="button"
          class="aspect-square rounded-lg flex items-center justify-center text-xl transition-colors duration-150"
          :class="
            icon === name
              ? 'bg-brand-tint text-brand ring-2 ring-brand'
              : 'text-ink-muted hover:bg-surface-hover hover:text-ink'
          "
          @click="icon = name"
        >
          <i :class="`mdi mdi-${name}`" />
        </button>
      </div>
    </FormField>
  </FormDialog>
</template>
