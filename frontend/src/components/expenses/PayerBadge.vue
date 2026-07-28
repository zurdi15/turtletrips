<script setup lang="ts">
import { computed } from 'vue'
import MemberChip from '../MemberChip.vue'
import Pill from '../ui/Pill.vue'
import type { Expense, Traveler } from '../../api/types'

// Quién pagó un gasto, igual en la tabla y en la lista móvil: chip del viajero
// (con su avatar), pill ámbar si salió del fondo común y, si no hay pagador, lo
// que ponga el slot (un guion en la tabla, nada en la lista).
const props = defineProps<{ expense: Expense; memberById: Map<number, Traveler> }>()

const member = computed(() =>
  props.expense.paid_by_id != null
    ? (props.memberById.get(props.expense.paid_by_id) ?? null)
    : null,
)
</script>

<template>
  <Pill
    v-if="expense.paid_by_common"
    color="warn"
    icon="pi pi-wallet"
    v-tooltip.top="$t('expenses.table.commonTooltip')"
  >
    {{ $t('expenses.table.commonPill') }}
  </Pill>
  <MemberChip v-else-if="member" :member="member" />
  <slot v-else />
</template>
