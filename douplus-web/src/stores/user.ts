import { defineStore } from 'pinia'
import { ref } from 'vue'
import { login as loginApi, getUserInfo } from '@/api/auth'
import type { UserInfo } from '@/api/types'

export const useUserStore = defineStore('user', () => {
  const token = ref<string>(localStorage.getItem('token') || '')
  const userInfo = ref<UserInfo | null>(null)

  const setToken = (newToken: string) => {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  const clearToken = () => {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
  }

  const login = async (username: string, password: string) => {
    const res = await loginApi({ username, password })
    if (res.code === 200 && res.data) {
      setToken(res.data.accessToken)
      userInfo.value = res.data.user
      return true
    }
    return false
  }

  const fetchUserInfo = async () => {
    if (!token.value) return
    try {
      const res = await getUserInfo()
      if (res.code === 200 && res.data) {
        userInfo.value = res.data
      }
    } catch (error) {
      clearToken()
    }
  }

  const logout = () => {
    clearToken()
  }

  return {
    token,
    userInfo,
    setToken,
    clearToken,
    login,
    fetchUserInfo,
    logout
  }
})
