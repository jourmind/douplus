import { get, post } from '@/utils/request'
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
}) => {
  return get('/douplus/task/page', params)
}

/**
 * 取消投放任务
 */
export const cancelTask = (id: number) => {
  return post(`/douplus/task/${id}/cancel`)
}

/**
 * 获取任务详情
 */
export const getTaskDetail = (id: number) => {
  return get(`/douplus/task/${id}`)
}