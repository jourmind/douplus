import { get, post, postLong, del } from '@/utils/request'
import type { DouplusTask, CreateTaskRequest } from './types'

/**
 * 创建投放任务（支持单个或批量）
 */
export const createTask = (requests: CreateTaskRequest[]) => {
  return post<DouplusTask[]>('/douplus/task/create', requests)
}

/**
 * 创建单个投放任务
 */
export const createSingleTask = (request: CreateTaskRequest) => {
  return post<DouplusTask>('/douplus/task/create-single', request)
}

/**
 * 分页查询投放记录
 */
export const getTaskPage = (params: {
  pageNum?: number
  pageSize?: number
  status?: string
  sortField?: string
  sortOrder?: string
}) => {
  return get('/douplus/task/page', params)
}

/**
 * 查询指定账号的投放记录
 */
export const getTaskList = (params: {
  accountId?: number
  pageNum?: number
  pageSize?: number
  status?: string
  sortField?: string
  sortOrder?: string
}) => {
  return get('/douplus/task/page', params)
}

/**
 * 获取指定账号的订单统计数据
 */
export const getAccountStats = (accountId: number, params?: {
  period?: 'today' | '7d' | '30d' | 'all'
}) => {
  return get(`/douplus/task/stats/${accountId}`, params)
}

/**
 * 获取用户所有账号的汇总统计数据
 */
export const getAllAccountsStats = (params?: {
  period?: 'today' | '7d' | '30d' | 'all'
  accountId?: number
}) => {
  return get('/douplus/task/stats', params)
}

/**
 * 获取指定账号下的视频维度统计列表
 */
export const getVideoStatsByAccount = (accountId: number, params?: {
  period?: 'today' | '7d' | '30d' | 'all'
  sortBy?: 'cost' | 'playCount' | 'likeCount' | 'shareCount' | 'convertCount' | 'playPer100Cost'
  sortOrder?: 'asc' | 'desc'
  pageNum?: number
  pageSize?: number
}) => {
  return get(`/douplus/video/stats/${accountId}`, params)
}

/**
 * 获取所有账号的视频维度统计列表（汇总）
 */
export const getAllVideoStats = (params?: {
  period?: 'today' | '7d' | '30d' | 'all'
  accountId?: number
  sortBy?: 'cost' | 'playCount' | 'likeCount' | 'shareCount' | 'convertCount' | 'playPer100Cost'
  sortOrder?: 'asc' | 'desc'
  pageNum?: number
  pageSize?: number
}) => {
  return get('/douplus/video/stats/all', params)
}

/**
 * 取消投放任务
 */
export const cancelTask = (id: number) => {
  return post(`/douplus/task/${id}/cancel`)
}

/**
 * 续费DOU+订单（追加预算和时长）
 */
export const renewTask = (data: {
  orderId: number
  budget: number
  duration: number
  investPassword: string
}) => {
  return post('/douplus/task/renew', data)
}

/**
 * 删除投放任务（仅可删除失败状态的任务）
 */
export const deleteTask = (id: number) => {
  return del(`/douplus/task/${id}`)
}

/**
 * 获取任务详情
 */
export const getTaskDetail = (id: number) => {
  return get(`/douplus/task/${id}`)
}

// 同步状态类型
export interface SyncStatus {
  status: 'idle' | 'syncing' | 'completed' | 'error'
  count: number
  message: string
}

/**
 * 同步单个账号的DOU+历史订单（异步）
 */
export const syncOrders = (accountId: number) => {
  return postLong<SyncStatus>(`/douplus/task/sync/${accountId}`)
}

/**
 * 同步所有账号的DOU+历史订单（异步）
 */
export const syncAllOrders = () => {
  return postLong<SyncStatus>('/douplus/task/sync-all')
}

/**
 * 查询同步状态
 */
export const getSyncStatus = () => {
  return get<SyncStatus>('/douplus/task/sync-status')
}

/**
 * 获取视频标题列表（用于筛选器下拉选择）
 */
export const getVideoTitles = (params?: {
  accountId?: number
}) => {
  return get<{label: string, value: string}[]>('/douplus/video/titles', params)
}
