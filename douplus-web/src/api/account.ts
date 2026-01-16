import request from '@/utils/request'
import type { ApiResponse, PageResult, DouyinAccount } from './types'

// 获取账号列表
export function getAccountList(): Promise<ApiResponse<DouyinAccount[]>> {
  return request.get('/account/list')
}

// 分页查询账号
export function getAccountPage(pageNum: number, pageSize: number): Promise<ApiResponse<PageResult<DouyinAccount>>> {
  return request.get('/account/page', { params: { pageNum, pageSize } })
}

// 获取账号详情
export function getAccountById(id: number): Promise<ApiResponse<DouyinAccount>> {
  return request.get(`/account/${id}`)
}

// 更新账号备注
export function updateAccountRemark(id: number, remark: string): Promise<ApiResponse<void>> {
  return request.put(`/account/${id}/remark`, { remark })
}

// 更新单日限额
export function updateDailyLimit(id: number, dailyLimit: number): Promise<ApiResponse<void>> {
  return request.put(`/account/${id}/daily-limit`, { dailyLimit })
}

// 删除账号（解绑）
export function deleteAccount(id: number): Promise<ApiResponse<void>> {
  return request.delete(`/account/${id}`)
}

// 获取OAuth授权URL
export function getOAuthUrl(): Promise<ApiResponse<string>> {
  return request.get('/account/oauth/url')
}
