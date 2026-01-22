import axios from 'axios'
import type { AxiosResponse, InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import router from '@/router'

const request = axios.create({
  baseURL: '/api',
  timeout: 30000
})

// 请求拦截器
request.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const userStore = useUserStore()
    if (userStore.token) {
      config.headers.Authorization = `Bearer ${userStore.token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response: AxiosResponse) => {
    const res = response.data
    
    // 处理业务错误
    if (res.code !== 200) {
      ElMessage.error(res.message || '请求失败')
      
      // 未登录或Token过期
      if (res.code === 1001 || res.code === 1002 || res.code === 1003) {
        const userStore = useUserStore()
        userStore.clearToken()
        router.push('/login')
      }
      
      return Promise.reject(new Error(res.message || '请求失败'))
    }
    
    return res
  },
  (error) => {
    console.error('请求错误:', error)
    
    if (error.response?.status === 401) {
      const userStore = useUserStore()
      userStore.clearToken()
      router.push('/login')
      ElMessage.error('登录已过期，请重新登录')
    } else {
      ElMessage.error(error.message || '网络错误')
    }
    
    return Promise.reject(error)
  }
)

// API响应类型
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
  timestamp: number
}

// 封装 GET 请求
export function get<T>(url: string, params?: Record<string, any>): Promise<ApiResponse<T>> {
  return request.get(url, { params })
}

// 封装 POST 请求
export function post<T>(url: string, data?: any, config?: { timeout?: number }): Promise<ApiResponse<T>> {
  return request.post(url, data, config)
}

// 封装带长超时的 POST 请求（用于同步等耗时操作）
export function postLong<T>(url: string, data?: any): Promise<ApiResponse<T>> {
  return request.post(url, data, { timeout: 300000 }) // 5分钟超时
}

// 封装 DELETE 请求
export function del<T>(url: string): Promise<ApiResponse<T>> {
  return request.delete(url)
}

export default request
