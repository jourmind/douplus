import request from '@/utils/request'
import type { ApiResponse, PageResult, DouplusTask, CreateTaskRequest } from './types'

// 创建投放任务
export function createTask(data: CreateTaskRequest): Promise<ApiResponse<DouplusTask[]>> {
  return request.post('/douplus/task/create', data)
}

// 分页查询投放记录
export function getTaskPage(
  pageNum: number, 
  pageSize: number, 
  status?: string
): Promise<ApiResponse<PageResult<DouplusTask>>> {
  return request.get('/douplus/task/page', { 
    params: { pageNum, pageSize, status } 
  })
}

// 获取任务详情
export function getTaskById(id: number): Promise<ApiResponse<DouplusTask>> {
  return request.get(`/douplus/task/${id}`)
}

// 取消任务
export function cancelTask(id: number): Promise<ApiResponse<void>> {
  return request.post(`/douplus/task/${id}/cancel`)
}

// 获取统计数据
export function getTaskStats(): Promise<ApiResponse<{
  totalTasks: number
  successTasks: number
  failTasks: number
  runningTasks: number
  totalBudget: number
  totalCost: number
}>> {
  return request.get('/douplus/task/stats')
}
