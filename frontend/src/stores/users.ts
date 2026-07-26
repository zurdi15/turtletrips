import { defineStore } from 'pinia'
import { api } from '../api/client'
import type { User, UserCreateInput, UserUpdateInput } from '../api/types'
import { useGlobalResource } from './globalResource'

export const useUsersStore = defineStore('users', () => {
  const base = useGlobalResource<User, UserCreateInput, UserUpdateInput>({
    listPath: '/users',
    itemPath: (id) => `/users/${id}`,
    sort: (a, b) => a.username.localeCompare(b.username, 'es'),
  })

  function resetPassword(id: number, newPassword: string) {
    return api.post(`/users/${id}/password`, { new_password: newPassword })
  }

  return { ...base, resetPassword }
})
