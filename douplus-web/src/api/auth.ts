import request from '@/utils/request'
import type { ApiResponse, LoginResponse, UserInfo } from './types'

// 登录
export function login(data: { username: string; password: string }): Promise<ApiResponse<LoginResponse>> {
  return request.post('/auth/login', data)
}

// 获取用户信息
export function getUserInfo(): Promise<ApiResponse<UserInfo>> {
  return request.get('/auth/info')
}

// 修改密码
export function changePassword(data: { oldPassword: string; newPassword: string }): Promise<ApiResponse<void>> {
  return request.post('/auth/password', data)
}

// 设置投放密码
export function setInvestPassword(investPassword: string): Promise<ApiResponse<void>> {
  return request.post('/auth/invest-password', { investPassword })
}

// 验证投放密码
export function verifyInvestPassword(investPassword: string): Promise<ApiResponse<boolean>> {
  return request.post('/auth/verify-invest-password', { investPassword })
}

// 退出登录
export function logout(): Promise<ApiResponse<void>> {
  return request.post('/auth/logout')
}
